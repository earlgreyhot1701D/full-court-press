"""Tasks 2.4 and 2.5: the facts sheet and Game of the Night, on the golden set and on the
edge cases the design names (a failed reconciliation, overtime disagreement, ties)."""
import glob
import json
import os

import pytest

from zine.facts import build_facts
from zine.game_of_night import load_rules, pick, score

HERE = os.path.dirname(__file__)
GOLDEN = sorted(glob.glob(os.path.join(HERE, "..", "fixtures", "golden", "[0-9]*")))
STANDINGS = os.path.join(HERE, "..", "fixtures", "golden", "standings.json")
needs_golden = pytest.mark.skipif(not GOLDEN, reason="golden fixtures not fetched")
FORBIDDEN = ("odds", "spread", "moneyline", "prop", "injur", "betting")


def load(g):
    game = json.load(open(os.path.join(g, "game.json")))["data"]
    plays = json.load(open(os.path.join(g, "plays.json")))["data"]
    rl = {f.rsplit("_", 1)[1][:-5]: json.load(open(f))["data"] for f in glob.glob(os.path.join(g, "roster_*.json"))}
    return game, plays, rl


def golden_facts():
    st = json.load(open(STANDINGS))["data"]
    return {os.path.basename(g): build_facts(*load(g), st) for g in GOLDEN}


@needs_golden
def test_every_golden_game_builds_complete_facts():
    for gid, f in golden_facts().items():
        assert "missing" not in f, (gid, f.get("missing"))
        assert f["reconciled"]
        assert sum(f["quarters"]["home"]) == f["home"]["score"]
        assert f["the_number_key"] in f["numbers"]
        for side in ("home", "away"):
            assert f[side]["team"] in f["allowed_names"]
            assert str(f[side]["score"]) in f["allowed_numbers"]


@needs_golden
def test_the_game_day_is_the_eastern_calendar_day_not_utc():
    f = golden_facts()["25057"]
    assert f["tip_time_utc"] == "2026-09-18T02:00:00Z"
    assert f["date_local"] == "2026-09-17"


@needs_golden
def test_nothing_from_odds_props_or_injuries_reaches_the_facts():
    blob = json.dumps(golden_facts()).lower()
    for word in FORBIDDEN:
        assert word not in blob, word


@needs_golden
def test_every_stat_on_a_line_is_an_allowed_number():
    for f in golden_facts().values():
        allowed = set(f["allowed_numbers"])
        for line in f["player_lines"]:
            for k, v in line.items():
                if isinstance(v, int):
                    assert str(v) in allowed, (line["player"], k, v)


@needs_golden
def test_a_double_double_needs_both_categories_to_survive():
    for f in golden_facts().values():
        for n in f["notable"]:
            if n["type"] in ("double_double", "triple_double"):
                for word, cat in (("rebounds", "reb"), ("assists", "ast"), ("steals", "stl"), ("blocks", "blk")):
                    if word in n["detail"]:
                        assert cat not in f["dropped_categories"]


@needs_golden
def test_a_failed_reconciliation_publishes_no_stat_line():
    st = json.load(open(STANDINGS))["data"]
    game, plays, rl = load(GOLDEN[0])
    game = dict(game, home_score=game["home_score"] + 2)       # the feed now disagrees with itself
    f = build_facts(game, plays, rl, st)
    assert not f["reconciled"]
    assert "player_lines" not in f and "player_lines" in f["missing"]
    assert f["notable"] == [] and all(l["category"] != "points" for l in f["leaders"])


@needs_golden
def test_overtime_disagreement_is_left_out_not_guessed():
    st = json.load(open(STANDINGS))["data"]
    game, plays, rl = load(GOLDEN[0])
    f = build_facts(dict(game, period=6), plays, rl, st)
    assert "overtime_periods" not in f and "overtime_periods" in f["missing"]


# ---- Game of the Night --------------------------------------------------------------

def facts(gid, tip, margin=10, ot=0, notable=(), deficit=0):
    return {"game_id": gid, "tip_time_utc": tip, "final_margin": margin, "overtime_periods": ot,
            "notable": [{"type": t} for t in notable], "winner_max_deficit": deficit}


def test_rules_score_each_ingredient():
    r = load_rules()
    assert score(facts("a", "t", margin=3), r)[0] == r["close_margin_pts"]
    assert score(facts("a", "t", ot=1), r)[0] == r["overtime_pts"]
    assert score(facts("a", "t", notable=["30plus"]), r)[0] == r["thirty_pt_game_pts"]
    assert score(facts("a", "t", notable=["triple_double"]), r)[0] == r["triple_double_pts"]
    assert score(facts("a", "t", deficit=15), r)[0] == r["comeback_pts"]
    assert score(facts("a", "t"), r)[0] == 0


def test_a_tie_goes_to_the_later_tip():
    early = facts("early", "2026-09-20T23:00:00Z", margin=2)
    late = facts("late", "2026-09-21T02:00:00Z", margin=2)
    assert pick([early, late]) == "late"
    assert pick([late, early]) == "late"


def test_empty_slate_has_no_game_of_the_night():
    assert pick([]) is None


@needs_golden
def test_golden_pick_is_the_one_point_triple_double_game():
    assert pick(list(golden_facts().values())) == 25071


@needs_golden
def test_expansion_teams_get_their_full_names_and_no_name_is_blank():
    fs = golden_facts()
    assert fs["25057"]["home"]["team"] == "Portland Fire"
    assert fs["25066"]["home"]["team"] == "Toronto Tempo"
    for f in fs.values():
        assert all(n.strip() for n in f["allowed_names"])
        assert "Portland" in fs["25057"]["allowed_names"]


def test_team_fill_never_overrides_a_value_the_provider_supplied():
    from zine.league_config import complete_team
    real = {"abbreviation": "POR", "city": "Somewhere", "name": "Fire", "full_name": "Somewhere Fire"}
    assert complete_team(real) == real
    blank = {"abbreviation": "POR", "city": "", "name": "Fire", "full_name": "Fire"}
    assert complete_team(blank)["full_name"] == "Portland Fire"
    unknown = {"abbreviation": "XYZ", "city": "", "name": "Comets", "full_name": ""}
    assert complete_team(unknown)["full_name"] == "Comets"



@needs_golden
def test_plain_facts_state_quarter_winners_and_their_numbers_are_allowed():
    f = golden_facts()["25014"]
    assert "The Fever won the 4th quarter 17-9." in f["plain_facts"]
    assert "At halftime the Dream led 44-40." in f["plain_facts"]
    assert "The Fever went on an 8-0 run in overtime." in f["plain_facts"]
    assert "The Dream are 1st in the East at 30-14." in f["plain_facts"]
    assert "Allisha Gray had the game high with 32 points." in f["plain_facts"]
    g = golden_facts()["25071"]
    assert "Paige Bueckers led the Wings with 30 points." in g["plain_facts"]
    for n in ("44", "40", "72", "64"):
        assert n in f["allowed_numbers"]


@needs_golden
def test_every_plain_fact_passes_the_lock():
    from zine import fact_lock
    for gid, f in golden_facts().items():
        for sentence in f["plain_facts"]:
            out = {"headline": "x", "recap": sentence, "spotlight": {"player": f["player_lines"][0]["player"], "text": "x"},
                   "the_number_key": f["the_number_key"]}
            assert fact_lock.check(out, f)["sections"]["recap"] == "ok", (gid, sentence)
