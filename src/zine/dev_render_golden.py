"""Block 2 dev render (task 2.6): the five golden games, from real facts, to ./out-golden/.

No voice. Block 1's mock copy was invented sentences about invented numbers; on real games an
invented sentence would be about a real player, which is what the fact lock exists to stop. So
every voice section renders as "The writers' room passed on this one." until Block 3 wires the
model and the fact lock. Everything else on the page is deterministic and real.

Run: PYTHONPATH=src python -m zine.dev_render_golden
"""
import glob
import json
import os

from zine import contrast, render
from zine.dev_render_block1 import (dropped_labels, edition_urls, human_date, load_colors,
                                    max_run, read_url, spot_for, winner_loser)
from zine.facts import build_facts
from zine.game_of_night import pick

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
GOLDEN = os.path.join(ROOT, "fixtures", "golden")
OUT = os.path.join(ROOT, "out-golden")


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


def main():
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
            ctx = {"f": f, "edition": team["abbrev"], "voice": None, "the_number": the_number(f),
                   "is_game_of_night": f["game_id"] == gotn,
                   "audio": {"url": "#", "transcript": "Audio arrives in Block 5b."},
                   "edition_urls": edition_urls(f, "../../../"), "card_url": "card.png",
                   "slate": slate, "standings_movers": None, "spot_color": spot,
                   "on_spot_text": on_text, "low_contrast": low,
                   "date_display": human_date(f["date_local"]), "max_run": max_run(f),
                   "dropped_labels": dl_text, "dropped_count": dl_count,
                   "root_prefix": "../../../", "static_prefix": "../../../../static/"}
            d = os.path.join(OUT, "game", str(f["game_id"]), team["abbrev"])
            os.makedirs(d, exist_ok=True)
            p = os.path.join(d, "index.html")
            open(p, "w", encoding="utf-8").write(render.render("issue.html", ctx))
            written.append(p)
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
