"""Raw BALLDONTLIE responses -> the facts sheet. Pure: no network, no model.

The facts sheet is the only thing downstream reads: the templates render it, the voices are
given it, and the fact lock checks the voices against it. Every number a page can display is
in `numbers` and `allowed_numbers`; every name the AI may use is in `allowed_names`.

Inputs are the raw API shapes, unmodified: the game object, its plays, the two team rosters
from /players, and the standings rows. Built pieces: pbp_stats (the stat line), quarters,
runs, league_strip (standings) and timeline (true game order).

A required value that cannot be trusted is left out and named in `missing`. Never a guess.
"""
import re
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from zine.league_config import complete_team
from zine.league_strip import standings_line
from zine.pbp_stats import count
from zine.quarters import period_scores
from zine.runs import find_runs
from zine.timeline import in_game_order

# The calendar day of a game, for "the morning after", is the US Eastern date. A 7pm Pacific
# tip is 02:00 UTC the next day (game 25057), so the UTC date would file it under the wrong issue.
LEAGUE_TZ = ZoneInfo("America/New_York")

_STAT_WORDS = {"pts": "points", "reb": "rebounds", "ast": "assists", "stl": "steals", "blk": "blocks"}


def _slug(name):
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def _winner_max_deficit(plays, winner_is_home):
    """Largest deficit the winner overcame, from the scoreboard in true game order."""
    worst = 0
    for p in in_game_order(plays):
        hs, as_ = p.get("home_score"), p.get("away_score")
        if hs is None or as_ is None:
            continue
        gap = (as_ - hs) if winner_is_home else (hs - as_)
        worst = max(worst, gap)
    return worst


def build_facts(game, plays, roster_lists, standings_rows, league="wnba"):
    missing = []
    home_t, away_t = complete_team(game["home_team"], league), complete_team(game["visitor_team"], league)
    home = {"team": home_t["full_name"], "abbrev": home_t["abbreviation"], "score": game["home_score"]}
    away = {"team": away_t["full_name"], "abbrev": away_t["abbreviation"], "score": game["away_score"]}
    tip = datetime.fromisoformat(game["date"].replace("Z", "+00:00")).astimezone(timezone.utc)

    f = {
        "game_id": game["id"],
        "league": league,
        "date_local": tip.astimezone(LEAGUE_TZ).date().isoformat(),
        "season": game["season"],
        "season_type": "postseason" if game.get("postseason") else "regular",
        "tip_time_utc": tip.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": "Final" if game.get("status_state") == "final" else game.get("status"),
        "home": home,
        "away": away,
    }
    if home["score"] == away["score"]:
        missing.append("winner_abbrev")
    else:
        winner, loser = (home, away) if home["score"] > away["score"] else (away, home)
        f["winner_abbrev"] = winner["abbrev"]
        f["final_margin"] = winner["score"] - loser["score"]

    # stats from the play-by-play (Requirement 3b)
    st = count(plays, home, away, roster_lists)
    f["reconciled"] = st["reconciled"]
    f["dropped_categories"] = [c for c, v in st["categories"].items() if not v["ok"]]
    if f["dropped_categories"]:
        f["dropped_categories_note"] = "; ".join(
            "%s: %s" % (c, st["categories"][c]["reason"]) for c in f["dropped_categories"])
    if st["reconciled"]:
        f["player_lines"] = st["player_lines"]
    else:
        missing.append("player_lines")
        f["reconciliation"] = st["discrepancy"]          # owner-facing, never rendered

    # overtime: the game object and the plays must agree
    ot_game = max(0, (game.get("period") or 0) - 4)
    if ot_game == st["overtime_periods"]:
        f["overtime_periods"] = ot_game
    else:
        missing.append("overtime_periods")
        f["overtime_disagreement"] = {"game": ot_game, "plays": st["overtime_periods"]}

    q = period_scores(plays, home["score"], away["score"])
    if q:
        f["quarters"] = {"home": q["home"], "away": q["away"]}
    else:
        missing.append("quarters")

    f["runs"] = find_runs(plays, home["abbrev"], away["abbrev"])
    f["standings_line"] = standings_line(standings_rows, game["season"], {home["abbrev"], away["abbrev"]})
    if len(f["standings_line"]) != 2:
        missing.append("standings_line")
    if "winner_abbrev" in f:
        f["winner_max_deficit"] = _winner_max_deficit(plays, f["winner_abbrev"] == home["abbrev"])

    lines = f.get("player_lines", [])
    dropped = set(f["dropped_categories"])

    # leaders: top scorer per team; rebounds and assists only if those categories survived
    leaders = []
    for side in (home, away):
        team_lines = [l for l in lines if l["team_abbrev"] == side["abbrev"]]
        for stat in ("pts", "reb", "ast"):
            if stat in dropped or not team_lines:
                continue
            best = max(l[stat] for l in team_lines)
            if best <= 0:
                continue
            tied = sorted(l["player"] for l in team_lines if l[stat] == best)
            if len(tied) == 1:                            # a tie has no single leader; say nothing
                leaders.append({"player": tied[0], "team_abbrev": side["abbrev"],
                                "category": _STAT_WORDS[stat], "value": best})
    f["leaders"] = leaders

    # notable: 20+ and 30+ point games, the game high, and double-doubles only when every
    # category they rest on survived its gate (Requirement 3b)
    notable = []
    if lines:
        high = max(l["pts"] for l in lines)
        for l in lines:
            if l["pts"] >= 30:
                notable.append({"type": "30plus", "player": l["player"], "detail": "%d points" % l["pts"]})
            elif l["pts"] >= 20:
                notable.append({"type": "20plus", "player": l["player"], "detail": "%d points" % l["pts"]})
            if l["pts"] == high and sum(1 for x in lines if x["pts"] == high) == 1:
                notable.append({"type": "game_high", "player": l["player"], "detail": "%d points" % high})
            doubles = [s for s in ("pts", "reb", "ast", "stl", "blk") if s not in dropped and l.get(s, 0) >= 10]
            if len(doubles) >= 3:
                notable.append({"type": "triple_double", "player": l["player"],
                                "detail": ", ".join("%d %s" % (l[s], _STAT_WORDS[s]) for s in doubles)})
            elif len(doubles) == 2:
                notable.append({"type": "double_double", "player": l["player"],
                                "detail": ", ".join("%d %s" % (l[s], _STAT_WORDS[s]) for s in doubles)})
    f["notable"] = notable

    # numbers: every value a page may display, named
    nums = {"home_score": home["score"], "away_score": away["score"]}
    if "final_margin" in f:
        nums["margin"] = f["final_margin"]
    if f.get("overtime_periods"):
        nums["overtime_periods"] = f["overtime_periods"]
    for i, (h, a) in enumerate(zip(f.get("quarters", {}).get("home", []), f.get("quarters", {}).get("away", [])), 1):
        nums["q%d_home" % i], nums["q%d_away" % i] = h, a
    for r in f["runs"]:
        nums["run_%s_q%d_%s" % (r["team_abbrev"].lower(), r["quarter"], _slug(r["start_clock"]))] = r["points"]
    for ab, s in f["standings_line"].items():
        nums["%s_wins" % ab.lower()], nums["%s_losses" % ab.lower()] = s["wins"], s["losses"]
        nums["%s_conference_rank" % ab.lower()] = s["conference_rank"]
    for l in lines:
        for stat in ("pts", "fgm", "ftm", "reb", "ast", "stl", "blk", "to"):
            if stat in l:
                nums["%s_%s" % (_slug(l["player"]), stat)] = l[stat]
    if f.get("winner_max_deficit"):
        nums["winner_max_deficit"] = f["winner_max_deficit"]
    f["numbers"] = nums

    # what each candidate for The Number means, in plain words built only from facts
    team_name = {home["abbrev"]: home_t["name"], away["abbrev"]: away_t["name"]}
    period_word = lambda q: "overtime" if q > 4 else "the %s quarter" % ("1st", "2nd", "3rd", "4th")[q - 1]
    labels = {"margin": "point margin", "home_score": "%s points" % home_t["name"],
              "away_score": "%s points" % away_t["name"]}
    for r in f["runs"]:
        key = "run_%s_q%d_%s" % (r["team_abbrev"].lower(), r["quarter"], _slug(r["start_clock"]))
        labels[key] = "point run for the %s in %s" % (team_name[r["team_abbrev"]], period_word(r["quarter"]))
    for l in lines:
        for stat, word in _STAT_WORDS.items():
            if stat in l:
                labels["%s_%s" % (_slug(l["player"]), stat)] = "%s for %s" % (word, l["player"])
    if f.get("winner_max_deficit"):
        labels["winner_max_deficit"] = "point deficit the %s came back from" % team_name[f["winner_abbrev"]]
    f["number_labels"] = labels

    # a deterministic default for The Number; the voice may pick another key from `numbers`
    big_run = max(f["runs"], key=lambda r: r["points"], default=None)
    if big_run and big_run["points"] >= 10:
        f["the_number_key"] = "run_%s_q%d_%s" % (big_run["team_abbrev"].lower(), big_run["quarter"], _slug(big_run["start_clock"]))
    elif lines:
        f["the_number_key"] = "%s_pts" % _slug(lines[0]["player"])
    else:
        f["the_number_key"] = "margin" if "margin" in nums else "home_score"

    f["allowed_numbers"] = sorted({str(v) for v in nums.values()}, key=lambda s: (len(s), s))

    # names: team full names, cities, nicknames, abbreviations; every player on the stat line,
    # by full name and by surname only where that surname is unique in the game
    names = []
    for t in (home_t, away_t):
        names += [n for n in (t["full_name"], t.get("city"), t["name"], t["abbreviation"]) if (n or "").strip()]
    surnames = {}
    for l in lines:
        surnames.setdefault(l["player"].split()[-1], []).append(l["player"])
    for l in lines:
        names.append(l["player"])
        last = l["player"].split()[-1]
        if len(surnames[last]) == 1:
            names.append(last)
    f["allowed_names"] = list(dict.fromkeys(names))

    if missing:
        f["missing"] = missing
    return f
