"""Every file of the site as {site_path: (bytes, content_type)}. Pure: no network, no model, no AWS.

The deployed hunter and the local dev render both call this, so the golden set goes through the
same pipeline as live issues (Req 11.3). store.py writes the result to S3 or to a folder.

Layout (site-root relative):
  index.html, about/, archive/, team/<abbr>/            the live front, from the latest night
  <league>/<date>/<game_id>/<team>/index.html            The Call (default voice)
  <league>/<date>/<game_id>/<team>/film-room/index.html  The Film Room
  <league>/<date>/<game_id>/<team>/card.png, recap.mp3   share card, audio
  data/today.json, data/archive.json                      deterministic summaries only, no model text
  static/...                                             CSS, JS, fonts (shared by everything)
  golden/...                                             the same layout again, for the golden set

`prefix` is "" for live and "golden/" for the golden set.
"""
import json
import os

from zine import card, contrast, render, voice_view
from zine.pagekit import (DEFAULT_SPOT, dropped_labels, human_date, load_colors, max_run, spot_for,
                          winner_loser)
from zine.paths import STATIC, rel_root
from zine.voices import VOICE_ORDER

HTML = "text/html; charset=utf-8"
TYPES = {".css": "text/css; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".json": "application/json",
         ".ttf": "font/ttf", ".txt": "text/plain; charset=utf-8", ".png": "image/png", ".mp3": "audio/mpeg",
         ".svg": "image/svg+xml"}


GOLDEN_AT = "golden/"  # where the golden set lives; the local golden render sets "" (it is the root there)


def _ctx_paths(path, prefix):
    up = rel_root(path)
    # Social previews need an absolute image URL; SITE_URL is set on the Lambda. Without it
    # (local renders, tests) the default preview falls back to a relative path.
    site = os.environ.get("SITE_URL", "")
    og = (site + "static/og-default.png") if site else up + "static/og-default.png"
    return {"root_prefix": up + prefix, "static_prefix": up + "static/", "golden_url": up + GOLDEN_AT + "index.html",
            "og_default": og}


def slate_row(f, gotn_id, prefix=""):
    """Deterministic summary of one game for the index, archive, team pages and Around the League."""
    w, l = winner_loser(f)
    return {"game_id": f["game_id"], "league": f.get("league", "wnba"), "date_local": f["date_local"],
            "tip_time_utc": f.get("tip_time_utc", ""),
            "home": {k: f["home"][k] for k in ("team", "abbrev", "score")},
            "away": {k: f["away"][k] for k in ("team", "abbrev", "score")},
            "winner_abbrev": f["winner_abbrev"], "overtime": bool(f.get("overtime_periods")),
            "is_game_of_night": f["game_id"] == gotn_id,
            "winner_team": w["team"], "winner_score": w["score"], "loser_team": l["team"], "loser_score": l["score"],
            "editions": {t["abbrev"]: voice_view.issue_path(f, t["abbrev"], "the_call", prefix) for t in (f["home"], f["away"])},
            "read": voice_view.issue_path(f, f["winner_abbrev"], "the_call", prefix)}


def issue_files(f, results, gotn_id, day_rows, colors=None, audio=None, movers=None, prefix="", base_url=""):
    """Both editions, both voices, card and audio for one game.
    results: {(edition, voice): voice_run result or None}
    audio:   {edition: {"script": str, "mp3": bytes}} (missing edition = no player, Req 16.4)"""
    colors = colors or load_colors()
    files = {}
    for team in (f["home"], f["away"]):
        ed = team["abbrev"]
        spot = spot_for(colors, ed)
        on_text, _ratio, low = contrast.on_spot(spot)
        dl_text, dl_count = dropped_labels(f)
        folder = voice_view.issue_dir(f, ed, prefix)
        a = (audio or {}).get(ed)
        if a and a.get("mp3"):
            files[folder + "recap.mp3"] = (a["mp3"], TYPES[".mp3"])
        for voice in VOICE_ORDER:
            v = voice_view.build(results.get((ed, voice)), f)
            path = voice_view.issue_path(f, ed, voice, prefix)
            to_folder = "../" if voice_view.VOICE_SLUG[voice] else ""  # film-room/ sits one level down
            number = voice_view.the_number(f, v and v["number_key"])
            ctx = dict(_ctx_paths(path, prefix), **{
                "f": f, "edition": ed, "voice": v, "the_number": number,
                "voice_links": voice_view.voice_links(f, ed, voice, prefix),
                "edition_urls": voice_view.edition_urls(f, voice, prefix),
                "is_game_of_night": f["game_id"] == gotn_id,
                "audio": {"url": to_folder + "recap.mp3", "transcript": a["script"]} if a and a.get("mp3") else None,
                "card_url": (base_url + folder + "card.png") if base_url else to_folder + "card.png",
                "slate": day_rows, "standings_movers": movers, "spot_color": spot,
                "on_spot_text": on_text, "low_contrast": low, "date_display": human_date(f["date_local"]),
                "max_run": max_run(f), "dropped_labels": dl_text, "dropped_count": dl_count})
            files[path] = (render.render("issue.html", ctx).encode("utf-8"), HTML)
            if voice == VOICE_ORDER[0]:  # one card per edition, from the default voice
                files[folder + "card.png"] = (card.render(f, spot, v and v["headline"], number), TYPES[".png"])
    return files


def _index_card(row, page_path, colors):
    up = rel_root(page_path)
    home = dict(row["home"], spot=spot_for(colors, row["home"]["abbrev"]))
    away = dict(row["away"], spot=spot_for(colors, row["away"]["abbrev"]))
    return {"game_id": row["game_id"], "home": home, "away": away, "winner_abbrev": row["winner_abbrev"],
            "overtime": row["overtime"], "is_game_of_night": row["is_game_of_night"],
            "spot": spot_for(colors, row["winner_abbrev"]), "date_local": row["date_local"],
            "edition_urls": {k: up + p for k, p in row["editions"].items()}, "read_url": up + row["read"]}


def front_files(nights, colors=None, prefix="", label=None, front_rows=None):
    """Index, archive, team pages, about and data JSON from {date: [slate rows]}.
    front_rows overrides what the index shows (the golden set shows every game, not one night)."""
    colors = colors or load_colors()
    files = {}
    on_text, _r, low = contrast.on_spot(DEFAULT_SPOT)
    base = {"spot_color": None, "on_spot_text": on_text, "low_contrast": low}
    dates = sorted(nights, reverse=True)
    latest = front_rows if front_rows is not None else (nights[dates[0]] if dates else [])
    order = lambda rows: sorted(rows, key=lambda r: (not r["is_game_of_night"], r["tip_time_utc"]))

    p = prefix + "index.html"
    files[p] = (render.render("today.html", dict(base, **_ctx_paths(p, prefix), **{
        "date_display": label or (human_date(dates[0]) if dates else ""),
        "slate": [_index_card(r, p, colors) for r in order(latest)],
        "team_tabs": [{"abbrev": a, "spot": t["spot"]} for a, t in colors.items()],
        "ticker": [{"text": "%s %s . %s %s" % (r["winner_team"], r["winner_score"], r["loser_team"], r["loser_score"]),
                    "mark": "F/OT" if r["overtime"] else "F"} for r in order(latest)]})).encode("utf-8"), HTML)

    p = prefix + "archive/index.html"
    arch = [{"date_local": d, "count": len(nights[d]),
             "url": rel_root(p) + prefix + "archive/%s/index.html" % d} for d in dates]
    files[p] = (render.render("archive.html", dict(base, **_ctx_paths(p, prefix), dates=arch)).encode("utf-8"), HTML)
    for d in dates:  # one page per night, reusing the index layout
        p = prefix + "archive/%s/index.html" % d
        files[p] = (render.render("today.html", dict(base, **_ctx_paths(p, prefix), **{
            "date_display": human_date(d), "slate": [_index_card(r, p, colors) for r in order(nights[d])],
            "team_tabs": [], "ticker": []})).encode("utf-8"), HTML)

    p = prefix + "about/index.html"
    files[p] = (render.render("about.html", dict(base, **_ctx_paths(p, prefix))).encode("utf-8"), HTML)

    teams = {}
    for d in dates:
        for r in nights[d]:
            for side in ("home", "away"):
                teams.setdefault(r[side]["abbrev"], (r[side]["team"], []))[1].append(r)
    for ab, (name, rows) in sorted(teams.items()):
        p = prefix + "team/%s/index.html" % ab
        t_on, _tr, t_low = contrast.on_spot(spot_for(colors, ab))  # the header kicker sits on the team color
        files[p] = (render.render("team.html", dict(base, **_ctx_paths(p, prefix), **{
            "spot_color": spot_for(colors, ab), "on_spot_text": t_on, "low_contrast": t_low,
            "team": {"team": name, "abbrev": ab, "spot": spot_for(colors, ab)},
            "issues": [dict(_index_card(r, p, colors), date_local=r["date_local"]) for r in rows],
            "no_game_last_night": not any(r in latest for r in rows)})).encode("utf-8"), HTML)

    summary = lambda r: {k: r[k] for k in ("game_id", "date_local", "home", "away", "winner_abbrev", "overtime",
                                            "is_game_of_night", "editions", "read")}
    files[prefix + "data/today.json"] = (json.dumps([summary(r) for r in order(latest)]).encode("utf-8"), TYPES[".json"])
    files[prefix + "data/archive.json"] = (json.dumps({d: [summary(r) for r in order(nights[d])] for d in dates}).encode("utf-8"), TYPES[".json"])
    return files


def static_files():
    files = {}
    for dirpath, _dirs, names in os.walk(STATIC):
        for n in names:
            full = os.path.join(dirpath, n)
            rel = os.path.relpath(full, STATIC).replace(os.sep, "/")
            ext = os.path.splitext(n)[1].lower()
            if ext in TYPES:
                files["static/" + rel] = (open(full, "rb").read(), TYPES[ext])
    return files
