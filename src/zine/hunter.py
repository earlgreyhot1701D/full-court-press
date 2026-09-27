"""The morning job (Req 1). The handler only orchestrates; every outside service is passed in, so
`run` works offline in tests with fakes and a LocalStore.

    run(store, bdl, write, speak, today) -> summary

store  store.LocalStore or store.S3Store
bdl    bdl_client.Client (or a fake with .get / .get_all)
write  voice_client.write (or a fake)            model calls, capped by MAX_MODEL_CALLS_PER_RUN
speak  audio_client.speak (or a fake), or None    audio, capped by MAX_AUDIO_PER_RUN
today  the Pacific calendar date of this run

Dates: from the day after the marker through yesterday (Pacific), at most LOOKBACK_DAYS back.
The API files games by UTC date (confirmed on the real API, Sep 26 probe), so a US evening game
shows up under the next UTC day. Each night asks for that date and the next, then keeps games
whose US Eastern date matches. A night with no games is normal and advances the marker.

A night is rebuilt as a whole when it has a new Final, so Game of the Night and Around the League
stay consistent. Games already built reuse the cached feed and the cached voices: no new calls.
A game that fails is logged by id and error type and the marker does not pass its night (Req 1.5).
Logs carry ids, counts and lock rules only: never feed bodies, prompts, model text or keys.
"""
import json
import logging
import os
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from zine import audio_script, cache, site_build, state, voice_run
from zine.facts import LEAGUE_TZ, build_facts
from zine.game_of_night import pick
from zine.league_config import LEAGUES
from zine.store import publish
from zine.voices import VOICE_ORDER

log = logging.getLogger("fcp.hunter")
PACIFIC = ZoneInfo("America/Los_Angeles")
LOOKBACK_DAYS = 6


def dates_to_check(marker_date, today):
    yesterday = today - timedelta(days=1)
    start = yesterday if not marker_date else date.fromisoformat(marker_date) + timedelta(days=1)
    start = max(start, yesterday - timedelta(days=LOOKBACK_DAYS))
    out, d = [], start
    while d <= yesterday:
        out.append(d)
        d += timedelta(days=1)
    return out


def local_date(game):
    """US Eastern calendar date of a game from its tip time. The API's `date` is a real UTC tip
    time (probe, Sep 26: 00:00Z and 02:00Z Sep 25 are 8pm and 10pm Eastern on Sep 24), so it is
    always converted, midnight included. Only a bare YYYY-MM-DD is taken as a calendar date."""
    raw = game.get("date") or ""
    if len(raw) <= 10:
        return raw
    tip = datetime.strptime(raw[:19].replace(" ", "T"), "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
    return tip.astimezone(LEAGUE_TZ).date().isoformat()


def is_final(game):
    return (game.get("status_state") or "").lower() == "final" or (game.get("status") or "").lower() == "final"


def games_for_night(bdl, league, night):
    """-> (finals, pending_count, diag) for games whose US Eastern date is `night`.
    diag = {"asked": rows returned for this night's own date, "matched": games kept, "finals": n}."""
    seen, asked = {}, 0
    for i, d in enumerate((night, night + timedelta(days=1))):
        status, rows = bdl.get_all("/%s/v1/games?dates[]=%s&per_page=100" % (league, d.isoformat()))
        if status != 200:
            raise RuntimeError("games request failed: %s" % status)
        if i == 0:
            asked = len(rows)
        for g in rows:
            seen[g["id"]] = g
    mine = [g for g in seen.values() if local_date(g) == night.isoformat()]
    finals = [g for g in mine if is_final(g)]
    # The API files games by UTC date, so asking for UTC dates N and N+1 returns US Eastern nights
    # N-1 (late games), N, and N+1 (early games). Anything else means that model of the API broke.
    near = {(night + timedelta(days=k)).isoformat() for k in (-1, 0, 1)}
    stray = sum(1 for g in seen.values() if local_date(g) not in near)
    return finals, sum(1 for g in mine if not is_final(g)), {"asked": asked, "matched": len(mine),
                                                              "finals": len(finals), "stray": stray}


def game_inputs(store, bdl, league, game):
    """Feed data for one game: cached if present, else fetched and cached."""
    gid = game["id"]
    plays = cache.get_raw(store, league, gid, "plays")
    if plays is None:
        status, rows = bdl.get_all("/%s/v1/plays?game_id=%d&per_page=100" % (league, gid), max_pages=10)
        if status != 200:
            raise RuntimeError("plays request failed: %s" % status)
        plays = rows
        cache.put_raw(store, league, gid, "plays", plays)
    rosters = {}
    for side in ("home_team", "visitor_team"):
        t = game[side]
        rl = cache.get_raw(store, league, gid, "roster_" + t["abbreviation"])
        if rl is None:
            status, rl = bdl.get_all("/%s/v1/players?team_ids[]=%d&per_page=100" % (league, t["id"]))
            if status != 200:
                raise RuntimeError("roster request failed: %s" % status)
            cache.put_raw(store, league, gid, "roster_" + t["abbreviation"], rl)
        rosters[t["abbreviation"]] = rl
    cache.put_raw(store, league, gid, "game", game)
    return plays, rosters


def movers_line(prev, now_rows, names):
    """'Liberty up 1 to 4th in the East' style, deterministic, only when a previous snapshot exists."""
    if not prev:
        return None
    moves = []
    for ab, st in now_rows.items():
        before = prev.get(ab)
        if before and before != st["conference_rank"]:
            d = before - st["conference_rank"]
            moves.append("%s %s %d to %s" % (names.get(ab, ab), "up" if d > 0 else "down", abs(d), st["place"]))
    return "; ".join(moves) or None


def voices_for(store, write, f, budget):
    league, gid = f.get("league", "wnba"), f["game_id"]
    results = cache.get_voices(store, league, gid) or {}
    for t in (f["home"], f["away"]):
        for v in VOICE_ORDER:
            if results.get((t["abbrev"], v)) is None:
                r = voice_run.run(write, f, v, t["abbrev"], budget)
                results[(t["abbrev"], v)] = r if r["calls"] else None  # budget-skipped: retry next run
    cache.put_voices(store, league, gid, results)
    return results


def run(store, bdl, write, speak, today, env=None, nights=None):
    """nights: optional list of YYYY-MM-DD to (re)build regardless of the marker (recovery and
    verification). A forced run never moves the marker backwards."""
    env = env if env is not None else os.environ
    budget = voice_run.CallBudget(int(env.get("MAX_MODEL_CALLS_PER_RUN", 60)))
    audio_left = int(env.get("MAX_AUDIO_PER_RUN", 30))
    base_url = env.get("SITE_URL", "")
    leagues = [l for l in env.get("LEAGUES", "wnba").split(",") if LEAGUES.get(l, {}).get("enabled")]
    marker = state.read_marker(store)
    summary = {"built": [], "failed": [], "pending_nights": [], "nights": {}, "model_calls": 0, "audio": 0, "marker": {}}

    for league in leagues:
        st_status, st_rows = bdl.get_all("/%s/v1/standings" % league)
        standings = st_rows if st_status == 200 else []  # 401 or failure: scores-only strip (Req 9.3)
        prev_ranks = state.read_standings(store, league)
        new_ranks = {}
        advance_to = marker.get(league)
        blocked = False
        forced = [date.fromisoformat(n) for n in (nights or [])]
        for night in forced or dates_to_check(marker.get(league), today):
            ok_night = True
            try:
                finals, pending, diag = games_for_night(bdl, league, night)
            except Exception as e:
                summary["failed"].append({"night": night.isoformat(), "error": type(e).__name__})
                blocked = True
                continue
            summary["nights"][night.isoformat()] = diag
            if diag["stray"]:
                # a game outside the three nights a UTC query can return: the date model is wrong.
                # Hold the marker so no night is skipped for good. (A quiet night is not an error:
                # asking for UTC date N always returns the previous evening's late games.)
                summary["failed"].append({"night": night.isoformat(), "error": "UnmatchedGames"})
                ok_night = False
            if pending:
                summary["pending_nights"].append(night.isoformat())
                ok_night = False
            built = {r["game_id"] for r in state.load_night(store, league, night.isoformat())}
            if finals and (forced or any(g["id"] not in built for g in finals)):  # forced nights always rebuild
                facts_list = []
                for g in finals:
                    try:
                        plays, rosters = game_inputs(store, bdl, league, g)
                        f = build_facts(g, plays, rosters, standings, league)
                        facts_list.append(f)
                    except Exception as e:
                        summary["failed"].append({"game_id": g["id"], "error": type(e).__name__})
                        ok_night = False
                if facts_list:
                    for f in facts_list:
                        for ab, s in f.get("standings_line", {}).items():
                            new_ranks[ab] = s["conference_rank"]
                    # Pass 1: voices for every game first, so the Game of the Night can follow them:
                    # the front page never features a game whose winner's page lost its recap.
                    voiced = {}
                    for f in facts_list:
                        try:
                            voiced[f["game_id"]] = voices_for(store, write, f, budget)
                        except Exception as e:
                            summary["failed"].append({"game_id": f["game_id"], "error": type(e).__name__})
                            ok_night = False
                    facts_list = [f for f in facts_list if f["game_id"] in voiced]
                    gotn = pick(facts_list, eligible=site_build.featurable(facts_list, voiced))
                    rows = [site_build.slate_row(f, gotn, results=voiced[f["game_id"]]) for f in facts_list]
                    # Pass 2: audio and pages
                    for f in facts_list:
                        try:
                            results = voiced[f["game_id"]]
                            audio = {}
                            for t in (f["home"], f["away"]):
                                if speak and audio_left > 0:
                                    head = ((results.get((t["abbrev"], VOICE_ORDER[0])) or {}).get("sections") or {}).get("headline")
                                    script = audio_script.build(f, head)
                                    mp3 = speak(script)
                                    audio_left -= 1
                                    if mp3:
                                        audio[t["abbrev"]] = {"script": script, "mp3": mp3}
                                        summary["audio"] += 1
                            names = {f["home"]["abbrev"]: f["home"]["team"], f["away"]["abbrev"]: f["away"]["team"]}
                            movers = movers_line(prev_ranks, {ab: s for ab, s in f.get("standings_line", {}).items()}, names)
                            files = site_build.issue_files(f, results, gotn, rows, audio=audio, movers=movers, base_url=base_url)
                            publish(store, files)
                            summary["built"].append(f["game_id"])
                            for (ed, v), r in results.items():
                                if r:
                                    log.info(json.dumps({"game_id": f["game_id"], "edition": ed, "voice": v,
                                                         "calls": r["calls"], "lock": r["log"]}))
                        except Exception as e:
                            err = {"game_id": f["game_id"], "error": type(e).__name__}
                            if type(e).__name__ == "UndefinedError":  # names a template field, never model text
                                err["detail"] = str(e)[:120]
                            summary["failed"].append(err)
                            ok_night = False
                    published = set(summary["built"])
                    state.save_night(store, league, night.isoformat(), [r for r in rows if r["game_id"] in published])
            if ok_night and not blocked and not forced:
                advance_to = night.isoformat()
            else:
                blocked = True
        if new_ranks:
            state.write_standings(store, league, new_ranks)
        publish(store, site_build.front_files(state.nights(store, league)))
        publish(store, site_build.static_files())
        if advance_to:
            marker[league] = advance_to
        summary["marker"][league] = marker.get(league)
    state.write_marker(store, marker)
    summary["model_calls"] = int(env.get("MAX_MODEL_CALLS_PER_RUN", 60)) - budget.left
    log.info(json.dumps(summary))
    return summary


def handler(event, context):
    """Lambda entry point. The only place that builds the real clients."""
    for noisy in ("boto3", "botocore", "urllib3"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
    logging.getLogger().setLevel(os.environ.get("LOG_LEVEL", "INFO"))
    from zine import api_key, audio_client, voice_client
    from zine.bdl_client import Client
    from zine.store import S3Store
    store = S3Store(os.environ["BUCKET"])
    bdl = Client(api_key.get_key())
    today = datetime.now(PACIFIC).date()
    nights = (event or {}).get("nights") if isinstance(event, dict) else None  # {"nights": ["2026-09-25"]}
    return run(store, bdl, voice_client.write, audio_client.speak, today, nights=nights)
