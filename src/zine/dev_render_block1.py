"""Block 1 dev render: turn the mock fixtures into static HTML in ./out/ so the
design can be reviewed at CHECKPOINT 1. No backend, no AWS. This assembles the
view models the templates expect from the hand-written fixtures in
fixtures/mock/. It is Block 1 scaffolding; the real pipeline (facts.py,
voice_client.py, publish.py) arrives in later blocks.

Run: python -m zine.dev_render_block1   (from src/), or
     python src/zine/dev_render_block1.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render  # noqa: E402
import contrast  # noqa: E402

from datetime import date  # noqa: E402

# Category labels for the visible dropped-category note (design pass Sep 23, item 9).
CATEGORY_LABELS = {
    "reb": "Rebounds", "ast": "Assists", "stl": "Steals",
    "blk": "Blocks", "to": "Turnovers",
}


def human_date(iso):
    """'2026-09-19' -> 'SATURDAY, SEP 19, 2026' (design pass Sep 23, item 7)."""
    try:
        y, m, d = (int(x) for x in iso.split("-"))
        dt = date(y, m, d)
    except Exception:
        return iso
    days = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"]
    months = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
    return "%s, %s %d, %d" % (days[dt.weekday()], months[dt.month - 1], dt.day, dt.year)


def dropped_labels(f):
    """Return (labels_text, count) for the dropped-category note, or ("", 0)."""
    dropped = f.get("dropped_categories") or []
    names = [CATEGORY_LABELS.get(c, c) for c in dropped]
    if not names:
        return "", 0
    if len(names) == 1:
        return names[0], 1
    return (", ".join(names[:-1]) + " and " + names[-1]), len(names)


def max_run(f):
    runs = f.get("runs") or []
    return max((r.get("points", 0) for r in runs), default=1) or 1

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FIXTURES = os.path.join(ROOT, "fixtures", "mock")
OUT = os.path.join(ROOT, "out")
COLORS = os.path.join(ROOT, "static", "team_colors.json")

# Hand-written mock recap copy (Block 1 stands in for the model output; labeled).
MOCK_VOICE = {
    "mock-normal": {
        "label": "The Call",
        "headline": "Wings 87, Mercury 82",
        "recap": "Dallas won the second quarter 37 to 25 and spent the rest of the night holding the lead. Paige Bueckers finished with 26 points. Arike Ogunbowale added 22 with 6 assists. Phoenix got within 5, and that is where it ended, 87 to 82.",
        "spotlight": {
            "player": "Paige Bueckers", "initials": "PB", "team": "Dallas Wings",
            "text": "26 points, 4 rebounds, 5 assists.",
            "stats": [{"value": 26, "label": "PTS"}, {"value": 4, "label": "REB"}, {"value": 5, "label": "AST"}],
        },
    },
    "mock-overtime": {
        "label": "The Call",
        "headline": "Liberty 98, Aces 94 in overtime",
        "recap": "New York forced overtime with a 9 to 0 run and never trailed again. Sabrina Ionescu had 31 points and 7 assists. Jonquel Jones pulled 12 rebounds. Las Vegas got 28 from Jackie Young, but the Liberty closed it 98 to 94.",
        "spotlight": {
            "player": "Sabrina Ionescu", "initials": "SI", "team": "New York Liberty",
            "text": "31 points, 5 rebounds, 7 assists.",
            "stats": [{"value": 31, "label": "PTS"}, {"value": 5, "label": "REB"}, {"value": 7, "label": "AST"}],
        },
    },
    # mock-dropped-voice: no entry -> the writers' room passed on this one.
    "mock-category-gate-fail": {
        "label": "The Call",
        "headline": "Lynx 79, Storm 74",
        "recap": "Minnesota closed on a 10 to 2 run to hold off Seattle. Napheesa Collier led with 29 points. Nneka Ogwumike answered with 22 for the Storm, but the Lynx won it 79 to 74.",
        "spotlight": {
            "player": "Napheesa Collier", "initials": "NC", "team": "Minnesota Lynx",
            "text": "29 points, 8 rebounds.",
            "stats": [{"value": 29, "label": "PTS"}, {"value": 8, "label": "REB"}],
        },
    },
}

GOTN = "mock-overtime"  # mock Game of the Night


def load_colors():
    with open(COLORS, encoding="utf-8") as fh:
        return json.load(fh)["teams"]


def spot_for(colors, abbr):
    t = colors.get(abbr)
    return t["spot"] if t else "#FF48B0"


def edition_urls(f, root_prefix):
    gid = f["game_id"]
    return {
        f["home"]["abbrev"]: root_prefix + "game/%s/%s/index.html" % (gid, f["home"]["abbrev"]),
        f["away"]["abbrev"]: root_prefix + "game/%s/%s/index.html" % (gid, f["away"]["abbrev"]),
    }


def read_url(f, root_prefix):
    return root_prefix + "game/%s/%s/index.html" % (f["game_id"], f["winner_abbrev"])


def the_number_for(f):
    key = f.get("the_number_key")
    if not key or key not in f.get("numbers", {}):
        return None
    # Build a plain caption from a run, if the key names one.
    caption = "the game's decisive swing"
    for r in f.get("runs", []):
        if ("run_%s_q%s" % (r["team_abbrev"].lower(), r["quarter"])) == key:
            caption = "%s point run for %s in Q%s" % (r["points"], r["team_abbrev"], r["quarter"])
    return {"value": f["numbers"][key], "caption": caption}


def winner_loser(f):
    if f["winner_abbrev"] == f["home"]["abbrev"]:
        return f["home"], f["away"]
    return f["away"], f["home"]


def main():
    os.makedirs(OUT, exist_ok=True)
    colors = load_colors()

    fixtures = []
    for name in sorted(os.listdir(FIXTURES)):
        if name.endswith(".json"):
            with open(os.path.join(FIXTURES, name), encoding="utf-8") as fh:
                fixtures.append(json.load(fh))

    # slate for the index and the issue's Around-the-League block
    slate = []
    for f in fixtures:
        w, l = winner_loser(f)
        slate.append({
            "game_id": f["game_id"],
            "winner_team": w["team"], "winner_score": w["score"],
            "loser_team": l["team"], "loser_score": l["score"],
            "overtime": bool(f.get("overtime_periods")),
        })

    written = []

    # --- issue editions (both teams) for every fixture ---
    for f in fixtures:
        gid = f["game_id"]
        for team in (f["home"], f["away"]):
            edition = team["abbrev"]
            # out/game/<gid>/<edition>/index.html -> out/ root is 3 up
            root_prefix = "../../../"
            # static/ is a sibling of out/, so 4 up from the edition dir
            static_prefix = "../../../../static/"
            # spot color: the edition team's color if that team played (it did)
            spot = spot_for(colors, edition)
            on_text, ratio, low = contrast.on_spot(spot)
            dl_text, dl_count = dropped_labels(f)
            ctx = {
                "f": f,
                "edition": edition,
                "voice": MOCK_VOICE.get(gid) if not f.get("voice_dropped") else None,
                "the_number": the_number_for(f),
                "is_game_of_night": gid == GOTN,
                "audio": {"url": "#", "transcript": "Mock transcript. Audio arrives in Block 5b."},
                "edition_urls": edition_urls(f, root_prefix),
                "card_url": "card.png",
                "slate": slate,
                "standings_movers": None,
                "spot_color": spot,
                "on_spot_text": on_text,
                "low_contrast": low,
                "date_display": human_date(f["date_local"]),
                "max_run": max_run(f),
                "dropped_labels": dl_text,
                "dropped_count": dl_count,
                "root_prefix": root_prefix,
                "static_prefix": static_prefix,
            }
            html = render.render("issue.html", ctx)
            d = os.path.join(OUT, "game", gid, edition)
            os.makedirs(d, exist_ok=True)
            p = os.path.join(d, "index.html")
            with open(p, "w", encoding="utf-8") as fh:
                fh.write(html)
            written.append(p)

    # --- index ("All") ---
    index_slate = []
    for f in fixtures:
        rp = ""  # index is at out/index.html
        home = dict(f["home"]); home["spot"] = spot_for(colors, f["home"]["abbrev"])
        away = dict(f["away"]); away["spot"] = spot_for(colors, f["away"]["abbrev"])
        index_slate.append({
            "game_id": f["game_id"], "home": home, "away": away,
            "winner_abbrev": f["winner_abbrev"],
            "overtime": bool(f.get("overtime_periods")),
            "is_game_of_night": f["game_id"] == GOTN,
            "spot": spot_for(colors, f["winner_abbrev"]),
            "edition_urls": edition_urls(f, rp),
            "read_url": read_url(f, rp),
        })
    # Game of the Night first
    index_slate.sort(key=lambda g: (not g["is_game_of_night"],))
    team_tabs = [{"abbrev": a, "spot": t["spot"]} for a, t in colors.items()]
    idx_on_text, _idx_ratio, idx_low = contrast.on_spot("#FF48B0")  # default pink
    idx_ctx = {
        "date_display": human_date("2026-09-19"),
        "slate": index_slate,
        "team_tabs": team_tabs,
        "ticker": [{"text": "%s %s . %s %s" % (s["winner_team"], s["winner_score"], s["loser_team"], s["loser_score"]), "mark": "F"} for s in slate],
        "spot_color": None,
        "on_spot_text": idx_on_text,
        "low_contrast": idx_low,
        "root_prefix": "",            # index is at out/index.html
        "static_prefix": "../static/", # static/ is a sibling of out/
    }
    p = os.path.join(OUT, "index.html")
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(render.render("today.html", idx_ctx))
    written.append(p)

    # --- about --- (out/about/index.html: root is 1 up, static 2 up)
    ab_on_text, _ab_ratio, ab_low = contrast.on_spot("#FF48B0")
    about_ctx = {"root_prefix": "../", "static_prefix": "../../static/", "spot_color": None,
                 "on_spot_text": ab_on_text, "low_contrast": ab_low}
    d = os.path.join(OUT, "about")
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, "index.html")
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(render.render("about.html", about_ctx))
    written.append(p)

    print("wrote %d files:" % len(written))
    for w in written:
        print("  " + os.path.relpath(w, ROOT))


if __name__ == "__main__":
    main()
