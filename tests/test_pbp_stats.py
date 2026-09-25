"""Task 2.6b: statistics counted from play-by-play. Working tier: the golden set, plus the
failure paths the gates exist for. Fixtures are real BALLDONTLIE responses fetched Sep 24."""
import glob
import json
import os
import re

import pytest

from zine.pbp_stats import count

GOLDEN = sorted(glob.glob(os.path.join(os.path.dirname(__file__), "..", "fixtures", "golden", "[0-9]*")))


def load(g):
    game = json.load(open(os.path.join(g, "game.json")))["data"]
    plays = json.load(open(os.path.join(g, "plays.json")))["data"]
    rl = {f.rsplit("_", 1)[1][:-5]: json.load(open(f))["data"] for f in glob.glob(os.path.join(g, "roster_*.json"))}
    home = {"abbrev": game["home_team"]["abbreviation"], "score": game["home_score"]}
    away = {"abbrev": game["visitor_team"]["abbreviation"], "score": game["away_score"]}
    return game, plays, rl, home, away


@pytest.mark.skipif(not GOLDEN, reason="golden fixtures not fetched")
@pytest.mark.parametrize("g", GOLDEN, ids=[os.path.basename(g) for g in GOLDEN])
def test_golden_reconciles_and_credits_every_mention(g):
    game, plays, rl, home, away = load(g)
    r = count(plays, home, away, rl)
    assert r["reconciled"], r["discrepancy"]
    assert r["team_points"] == {home["abbrev"]: home["score"], away["abbrev"]: away["score"]}
    assert all(v == 0 for v in r["unattributed"].values())
    for text_key, stat in (("assists", "ast"), ("steals", "stl")):
        mentioned = sum(len(re.findall(r"\([^()]+? %s\)" % text_key, p["text"])) for p in plays)
        assert sum(l.get(stat, 0) for l in r["player_lines"]) == mentioned
    assert sum(l.get("blk", 0) for l in r["player_lines"]) == sum(" blocks " in p["text"] for p in plays)


@pytest.mark.skipif(not GOLDEN, reason="golden fixtures not fetched")
def test_overtime_from_plays_agrees_with_game_object():
    for g in GOLDEN:
        game, plays, rl, home, away = load(g)
        r = count(plays, home, away, rl)
        assert r["overtime_periods"] == max(0, game["period"] - 4)
    assert any(count(load(g)[1], load(g)[3], load(g)[4], load(g)[2])["overtime_periods"] > 0 for g in GOLDEN)


# ---- synthetic failure paths -------------------------------------------------------

H = {"abbreviation": "AAA"}
A = {"abbreviation": "BBB"}
ROSTERS = {"AAA": [{"first_name": "Ann", "last_name": "One"}, {"first_name": "Amy", "last_name": "Two"}],
           "BBB": [{"first_name": "Bea", "last_name": "Three"}]}


def play(text, team, typ="Jump Shot", scoring=False, value=0, period=1):
    return {"text": text, "team": team, "type": typ, "scoring_play": scoring, "score_value": value, "period": period}


def test_unknown_scorer_fails_the_points_gate_and_publishes_nothing():
    plays = [play("Ann One makes jumper", H, scoring=True, value=2),
             play("Zed Nobody makes jumper", A, scoring=True, value=2)]
    r = count(plays, {"abbrev": "AAA", "score": 2}, {"abbrev": "BBB", "score": 2}, ROSTERS)
    assert not r["reconciled"]
    assert r["player_lines"] == []
    assert r["discrepancy"]["unattributed_points"] == 2


def test_points_that_do_not_sum_to_the_final_score_fail():
    plays = [play("Ann One makes jumper", H, scoring=True, value=2)]
    r = count(plays, {"abbrev": "AAA", "score": 4}, {"abbrev": "BBB", "score": 0}, ROSTERS)
    assert not r["reconciled"]


def test_team_rebound_is_not_an_unattributed_player_event():
    plays = [play("AAA defensive team rebound", H, typ="Defensive Rebound"),
             play("Ann One defensive rebound", H, typ="Defensive Rebound")]
    r = count(plays, {"abbrev": "AAA", "score": 0}, {"abbrev": "BBB", "score": 0}, ROSTERS)
    assert r["unattributed"]["reb"] == 0
    assert r["categories"]["reb"]["ok"]


def test_steal_credited_to_own_team_drops_only_steals_and_they_are_absent_not_zero():
    plays = [play("Ann One makes jumper (Amy Two assists)", H, scoring=True, value=2),
             play("Ann One bad pass turnover (Amy Two steals)", H, typ="Bad Pass Turnover")]
    r = count(plays, {"abbrev": "AAA", "score": 2}, {"abbrev": "BBB", "score": 0}, ROSTERS)
    assert r["reconciled"]
    assert not r["categories"]["stl"]["ok"]
    assert r["categories"]["ast"]["ok"]
    for line in r["player_lines"]:
        assert "stl" not in line
        assert "ast" in line


def test_substitution_line_adds_a_player_missing_from_the_current_roster():
    plays = [play("Cat Four enters the game for Ann One", H, typ="Substitution"),
             play("Cat Four makes layup", H, scoring=True, value=2)]
    r = count(plays, {"abbrev": "AAA", "score": 2}, {"abbrev": "BBB", "score": 0}, ROSTERS)
    assert r["reconciled"]
    assert r["player_lines"][0]["player"] == "Cat Four"


def test_block_is_credited_to_the_other_team_and_counts_as_a_miss():
    plays = [play("Bea Three blocks Ann One's layup", H, typ="Layup Shot")]
    r = count(plays, {"abbrev": "AAA", "score": 0}, {"abbrev": "BBB", "score": 0}, ROSTERS)
    assert r["reconciled"]
    assert r["categories"]["blk"]["ok"], r["categories"]["blk"]
    assert [l["blk"] for l in r["player_lines"] if l["player"] == "Bea Three"] == [1]


def test_more_blocks_than_opponent_misses_drops_blocks():
    # the same shooter cannot be blocked twice on one miss: two blocks, but only if both are misses
    plays = [play("Bea Three blocks Ann One's layup", H, typ="Layup Shot"),
             play("Bea Three blocks Amy Two's jumper", H, typ="Jump Shot")]
    r = count(plays, {"abbrev": "AAA", "score": 0}, {"abbrev": "BBB", "score": 0}, ROSTERS)
    assert r["categories"]["blk"]["ok"]      # two blocked shots are two misses, so the bound holds
