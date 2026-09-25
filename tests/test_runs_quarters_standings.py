"""Task 2.6c: runs, quarter scores and the standings line, against the golden set plus the two
traps found while building them (late-logged records, and a sum check that passes on wrong quarters)."""
import glob
import json
import os

import pytest

from zine.league_strip import standings_line
from zine.quarters import period_scores
from zine.runs import find_runs
from zine.timeline import clock_seconds, in_game_order

HERE = os.path.dirname(__file__)
GOLDEN = sorted(glob.glob(os.path.join(HERE, "..", "fixtures", "golden", "[0-9]*")))
STANDINGS = os.path.join(HERE, "..", "fixtures", "golden", "standings.json")
needs_golden = pytest.mark.skipif(not GOLDEN, reason="golden fixtures not fetched")


def load(g):
    game = json.load(open(os.path.join(g, "game.json")))["data"]
    plays = json.load(open(os.path.join(g, "plays.json")))["data"]
    return game, plays


def P(period, clock, h, a, text="x"):
    return {"period": period, "clock": clock, "home_score": h, "away_score": a, "text": text}


# ---- timeline -----------------------------------------------------------------------

def test_clock_parsing():
    assert clock_seconds("7:52") == 472
    assert clock_seconds("18.3") == 18.3
    assert clock_seconds(None) is None


def test_late_record_is_put_back_where_it_happened():
    plays = [P(1, "5:00", 2, 0), P(1, "0:10", 6, 0), P(1, "2:00", 4, 0)]   # 2:00 logged late
    assert [p["clock"] for p in in_game_order(plays)] == ["5:00", "2:00", "0:10"]


@needs_golden
def test_score_never_goes_down_in_true_order():
    for g in GOLDEN:
        _, plays = load(g)
        top = (0, 0)
        for p in in_game_order(plays):
            assert p["home_score"] >= top[0] and p["away_score"] >= top[1], (g, p["order"])
            top = (p["home_score"], p["away_score"])


# ---- quarters -----------------------------------------------------------------------

@needs_golden
def test_quarters_add_up_and_overtime_has_a_fifth_period():
    for g in GOLDEN:
        game, plays = load(g)
        q = period_scores(plays, game["home_score"], game["away_score"])
        assert q is not None, g
        assert sum(q["home"]) == game["home_score"] and sum(q["away"]) == game["away_score"]
        assert q["periods"] == max(4, game["period"])


@needs_golden
def test_late_record_no_longer_bends_a_quarter():
    # 25057: a late 20-20 record filed under Q1 once made Q1 read 20-20; it ended 26-20 Portland
    g = [x for x in GOLDEN if x.endswith("25057")]
    if not g:
        pytest.skip("25057 not in golden set")
    game, plays = load(g[0])
    q = period_scores(plays, game["home_score"], game["away_score"])
    assert (q["home"][0], q["away"][0]) == (26, 20)


def test_a_score_that_goes_down_returns_none():
    plays = [P(1, "5:00", 10, 0), P(1, "4:00", 8, 0), P(2, "5:00", 12, 0)]  # same clock order, score drops
    assert period_scores(plays, 12, 0) is None


def test_quarters_that_do_not_add_up_return_none():
    assert period_scores([P(1, "0:00", 10, 8)], 12, 8) is None


# ---- runs ---------------------------------------------------------------------------

def test_a_run_never_crosses_a_period_boundary():
    plays = [P(1, "1:00", 3, 0), P(1, "0:30", 6, 0), P(2, "9:30", 9, 0), P(2, "9:00", 12, 0)]
    runs = find_runs(plays, "HOME", "AWAY")
    assert all(r["points"] < 8 for r in runs)      # 6 + 6 across the break is not a 12-0 run


def test_an_unanswered_stretch_is_a_run():
    plays = [P(1, "6:00", 3, 0), P(1, "5:00", 5, 0), P(1, "4:00", 8, 0), P(1, "3:00", 8, 2)]
    runs = find_runs(plays, "HOME", "AWAY")
    assert [(r["team_abbrev"], r["points"], r["detail"]) for r in runs] == [("HOME", 8, "8-0")]


@needs_golden
def test_golden_runs_have_real_duration_and_stay_in_one_period():
    for g in GOLDEN:
        game, plays = load(g)
        for r in find_runs(plays, game["home_team"]["abbreviation"], game["visitor_team"]["abbreviation"]):
            assert r["points"] >= 8
            assert clock_seconds(r["start_clock"]) > clock_seconds(r["end_clock"]), (g, r)


# ---- standings ----------------------------------------------------------------------

@needs_golden
def test_standings_filter_to_the_season_and_publish_a_place_not_a_seed():
    rows = json.load(open(STANDINGS))["data"]
    line = standings_line(rows, 2026, {"SEA", "TOR", "ATL"})
    assert line["SEA"]["place"] == "8th in the West"
    assert line["TOR"]["place"] == "6th in the East"
    assert line["ATL"]["place"] == "1st in the East"
    for v in line.values():
        assert "playoff_seed" not in v
    assert standings_line(rows, 1999, {"SEA"}) == {}


def test_a_team_with_two_rows_for_a_season_is_left_out():
    row = {"season": 2026, "team": {"abbreviation": "AAA"}, "wins": 1, "losses": 1,
           "conference": "Eastern Conference", "playoff_seed": 1}
    assert standings_line([row, dict(row)], 2026, {"AAA"}) == {}
