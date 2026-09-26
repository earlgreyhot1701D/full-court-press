"""Small pure helpers the page builders share: dates for display, the dropped-category note,
team colors. Moved out of dev_render_block1 so production code never imports a dev script."""
import json
import os
from datetime import date

from zine.paths import STATIC

CATEGORY_LABELS = {"reb": "Rebounds", "ast": "Assists", "stl": "Steals", "blk": "Blocks", "to": "Turnovers"}
DEFAULT_SPOT = "#FF48B0"


def human_date(iso):
    """'2026-09-19' -> 'SATURDAY, SEP 19, 2026'."""
    try:
        y, m, d = (int(x) for x in iso.split("-"))
        dt = date(y, m, d)
    except Exception:
        return iso
    days = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"]
    months = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
    return "%s, %s %d, %d" % (days[dt.weekday()], months[dt.month - 1], dt.day, dt.year)


def dropped_labels(f):
    names = [CATEGORY_LABELS.get(c, c) for c in (f.get("dropped_categories") or [])]
    if not names:
        return "", 0
    if len(names) == 1:
        return names[0], 1
    return ", ".join(names[:-1]) + " and " + names[-1], len(names)


def max_run(f):
    return max((r.get("points", 0) for r in f.get("runs") or []), default=1) or 1


def load_colors():
    with open(os.path.join(STATIC, "team_colors.json"), encoding="utf-8") as fh:
        return json.load(fh)["teams"]


def spot_for(colors, abbr):
    t = colors.get(abbr)
    return t["spot"] if t else DEFAULT_SPOT


def winner_loser(f):
    return (f["home"], f["away"]) if f["winner_abbrev"] == f["home"]["abbrev"] else (f["away"], f["home"])
