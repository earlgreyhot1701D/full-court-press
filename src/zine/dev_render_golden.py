"""Block 2 dev render (task 2.6): the five golden games, from real facts, to ./out-golden/.

Voices: every golden game renders both voice pages per edition. Game 25071 runs Claude's
hand-written stand-ins (fixtures/voice_standins/25071.json) through the real voice_run flow and
fact lock, with a fake in place of the model. Every other game has no stand-in, so its voice
sections show "The writers' room passed on this one." Local dev only; out-golden/ is gitignored
and never published. The real model replaces the fake in task 3.5.

Run: PYTHONPATH=src python -m zine.dev_render_golden
"""
import glob
import json
import os

from zine import card, contrast, render, voice_run, voice_view
from zine.voices import VOICE_ORDER
from zine.dev_render_block1 import (dropped_labels, edition_urls, human_date, load_colors,
                                    max_run, read_url, spot_for, winner_loser)
from zine.facts import build_facts
from zine.game_of_night import pick

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
GOLDEN = os.path.join(ROOT, "fixtures", "golden")
OUT = os.path.join(ROOT, "out-golden")
STANDINS = os.path.join(ROOT, "fixtures", "voice_standins")


def standin_result(f, edition, voice):
    """Run the stand-in through the real flow with a fake model, or None if there is none."""
    p = os.path.join(STANDINS, "%s.json" % f["game_id"])
    if not os.path.exists(p):
        return None
    answer = json.load(open(p, encoding="utf-8")).get(edition, {}).get(voice)
    if answer is None:
        return None
    return voice_run.run(lambda system, messages: dict(answer), f, voice, edition)


def the_number(f):
    key = f.get("the_number_key")
    if key not in f.get("numbers", {}):
        return None
    return {"value": f["numbers"][key], "caption": f.get("number_labels", {}).get(key, "")}


def load_all():
    standings = json.load(open(os.path.join(GOLDEN, "standings.json")))["data"]
    out = []
    for g in sorted(glob.glob(os.path.join(GOLDEN, "[0-9]*"))):
        game = json.load(open(os.path.join(g, "game.json")))["data"]
        plays = json.load(open(os.path.join(g, "plays.json")))["data"]
        rl = {p.rsplit("_", 1)[1][:-5]: json.load(open(p))["data"] for p in glob.glob(os.path.join(g, "roster_*.json"))}
        out.append(build_facts(game, plays, rl, standings))
    return out


def main(result_fn=None):
    """result_fn(f, edition, voice) -> voice_run result or None. Default: the stand-ins."""
    result_fn = result_fn or standin_result
    colors = load_colors()
    facts = load_all()
    gotn = pick(facts)
    slate = []
    for f in facts:
        w, l = winner_loser(f)
        slate.append({"game_id": f["game_id"], "winner_team": w["team"], "winner_score": w["score"],
                      "loser_team": l["team"], "loser_score": l["score"],
                      "overtime": bool(f.get("overtime_periods"))})
    written = []
    for f in facts:
        for team in (f["home"], f["away"]):
            spot = spot_for(colors, team["abbrev"])
            on_text, _ratio, low = contrast.on_spot(spot)
            dl_text, dl_count = dropped_labels(f)
            for voice in VOICE_ORDER:
                v = voice_view.build(result_fn(f, team["abbrev"], voice), f)
                pre = voice_view.root_prefix(voice)
                ctx = {"f": f, "edition": team["abbrev"], "voice": v,
                       "the_number": voice_view.the_number(f, v and v["number_key"]),
                       "voice_links": voice_view.voice_links(f, team["abbrev"], voice),
                       "is_game_of_night": f["game_id"] == gotn,
                       "audio": {"url": "#", "transcript": "Audio arrives in Block 5b."},
                       "edition_urls": voice_view.edition_urls(f, voice),
                       "card_url": ("../" if voice != VOICE_ORDER[0] else "") + "card.png",
                       "slate": slate, "standings_movers": None, "spot_color": spot,
                       "on_spot_text": on_text, "low_contrast": low,
                       "date_display": human_date(f["date_local"]), "max_run": max_run(f),
                       "dropped_labels": dl_text, "dropped_count": dl_count,
                       "root_prefix": pre, "static_prefix": pre + "../static/"}
                p = os.path.join(OUT, *voice_view.page_path(f["game_id"], team["abbrev"], voice).split("/"))
                os.makedirs(os.path.dirname(p), exist_ok=True)
                open(p, "w", encoding="utf-8").write(render.render("issue.html", ctx))
                written.append(p)
                if voice == VOICE_ORDER[0]:  # one card per edition, from the default voice
                    png = card.render(f, spot, v and v["headline"], ctx["the_number"])
                    open(os.path.join(os.path.dirname(p), "card.png"), "wb").write(png)
    idx = []
    for f in sorted(facts, key=lambda f: (f["game_id"] != gotn, f["tip_time_utc"])):
        home = dict(f["home"], spot=spot_for(colors, f["home"]["abbrev"]))
        away = dict(f["away"], spot=spot_for(colors, f["away"]["abbrev"]))
        idx.append({"game_id": f["game_id"], "home": home, "away": away, "winner_abbrev": f["winner_abbrev"],
                    "overtime": bool(f.get("overtime_periods")), "is_game_of_night": f["game_id"] == gotn,
                    "spot": spot_for(colors, f["winner_abbrev"]), "edition_urls": edition_urls(f, ""),
                    "read_url": read_url(f, "")})
    on_text, _r, low = contrast.on_spot("#FF48B0")
    ctx = {"date_display": "Golden set, five real games", "slate": idx,
           "team_tabs": [{"abbrev": a, "spot": t["spot"]} for a, t in colors.items()],
           "ticker": [{"text": "%s %s . %s %s" % (s["winner_team"], s["winner_score"], s["loser_team"], s["loser_score"]),
                       "mark": "F/OT" if s["overtime"] else "F"} for s in slate],
           "spot_color": None, "on_spot_text": on_text, "low_contrast": low,
           "root_prefix": "", "static_prefix": "../static/"}
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, "index.html")
    open(p, "w", encoding="utf-8").write(render.render("today.html", ctx))
    written.append(p)
    print("Game of the Night:", gotn)
    for w in written:
        print(" ", os.path.relpath(w, ROOT))


if __name__ == "__main__":
    main()
