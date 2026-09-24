"""Render-time contrast check (design/RENDER-CONTRAST.md). Walks all 15 teams
and asserts the chosen text colour reaches 4.5:1 against that team's spot colour,
or that low-contrast is flagged so the .spot-surface escape hatch fires. This is
the check that catches a new team's colour being added without anyone looking at
the page.

Run: python -m pytest tests/test_contrast.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src", "zine"))
import contrast  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COLORS = os.path.join(ROOT, "static", "team_colors.json")

# Verified figures from design/RENDER-CONTRAST.md (chosen text colour per team).
EXPECTED_TEXT = {
    "DAL": "paper", "NY": "ink", "GS": "ink", "LV": "paper", "CHI": "ink",
}


def _teams():
    with open(COLORS, encoding="utf-8") as fh:
        return json.load(fh)["teams"]


def test_every_team_is_readable():
    teams = _teams()
    assert len(teams) == 15
    for abbr, info in teams.items():
        text, ratio, low = contrast.on_spot(info["spot"])
        # Either the chosen text clears AA, or low-contrast is flagged so the
        # escape hatch pulls text off the colour entirely. Never silently unreadable.
        assert ratio >= 4.5 or low, (
            "%s (%s): chosen %s only %.1f:1 and low_contrast not set" % (abbr, info["spot"], text, ratio)
        )


def test_matches_documented_choices():
    teams = _teams()
    for abbr, want in EXPECTED_TEXT.items():
        text, ratio, low = contrast.on_spot(teams[abbr]["spot"])
        assert text == want, "%s: expected %s, got %s (%.1f:1)" % (abbr, want, text, ratio)


def test_default_pink_is_ink():
    text, ratio, low = contrast.on_spot("#FF48B0")
    assert text == "ink"
    assert not low


if __name__ == "__main__":
    teams = _teams()
    print("%-4s %-9s %-6s %6s %s" % ("ABBR", "SPOT", "TEXT", "RATIO", "LOWC"))
    for abbr, info in teams.items():
        text, ratio, low = contrast.on_spot(info["spot"])
        print("%-4s %-9s %-6s %6.1f %s" % (abbr, info["spot"], text, ratio, low))
