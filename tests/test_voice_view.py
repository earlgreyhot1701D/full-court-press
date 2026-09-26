"""Task 3.5 prep: one page per voice, the switcher, and section-by-section drops on the page."""
import copy

import pytest

from zine import render, voice_run, voice_view
from test_fact_lock import CLEAN
from test_facts_gotn import golden_facts, needs_golden


@pytest.fixture(scope="module")
def f71():
    return golden_facts()["25071"]


def page(f, result, voice="the_call", edition="PHX"):
    v = voice_view.build(result, f)
    ctx = {"f": f, "edition": edition, "voice": v,
           "the_number": voice_view.the_number(f, v and v["number_key"]),
           "voice_links": voice_view.voice_links(f, edition, voice),
           "edition_urls": voice_view.edition_urls(f, voice), "is_game_of_night": False,
           "audio": None, "card_url": "card.png", "slate": [], "standings_movers": None,
           "spot_color": "#201747", "on_spot_text": "#FFFFFF", "low_contrast": False,
           "date_display": "x", "max_run": max([r["points"] for r in f["runs"]] or [1]), "dropped_labels": "", "dropped_count": 0,
           "root_prefix": voice_view.root_prefix(voice), "static_prefix": "static/"}
    return render.render("issue.html", ctx)


def run(f, *answers, voice="the_call"):
    q = [copy.deepcopy(a) for a in answers]
    return voice_run.run(lambda s, m: q.pop(0), f, voice, "PHX")


@needs_golden
def test_urls_default_voice_is_the_call(f71):
    assert voice_view.page_path(25071, "PHX", "the_call") == "game/25071/PHX/index.html"
    assert voice_view.page_path(25071, "PHX", "film_room") == "game/25071/PHX/film-room/index.html"
    links = voice_view.voice_links(f71, "PHX", "film_room")
    assert [l["label"] for l in links] == ["The Call", "The Film Room"]
    assert links[0]["url"] == "../../../../game/25071/PHX/index.html" and links[1]["current"]


@needs_golden
def test_clean_voice_renders_every_section(f71):
    html = page(f71, run(f71, CLEAN))
    assert CLEAN["headline"] in html and "writers" not in html
    assert "Spotlight" in html and "by The Call" in html
    assert 'aria-label="Voice"' in html and 'aria-current="page">The Call<' in html


@needs_golden
def test_dropped_recap_shows_writers_room_and_keeps_the_rest(f71):
    bad = dict(CLEAN, recap="Kahleah Copper scored 33 points.")
    html = page(f71, run(f71, bad, bad))
    assert "The writers&rsquo; room passed on this one." in html
    assert CLEAN["headline"] in html and "33 points" not in html


@needs_golden
def test_dropped_headline_falls_back_to_score_line(f71):
    bad = dict(CLEAN, headline="Copper drops 44")
    html = page(f71, run(f71, bad, bad))
    assert "Copper drops 44" not in html and "Phoenix Mercury 87, Dallas Wings 86" in html


@needs_golden
def test_dropped_number_uses_facts_default(f71):
    bad = dict(CLEAN, the_number_key="made_up")
    v = voice_view.build(run(f71, bad, bad), f71)
    n = voice_view.the_number(f71, v["number_key"])
    assert n["key"] == f71["the_number_key"] and n["caption"]


@needs_golden
def test_whole_voice_dropped(f71):
    html = page(f71, None)
    assert "The writers&rsquo; room passed on this one." in html and "Spotlight" not in html


@needs_golden
def test_spotlight_stats_come_from_facts_not_the_model(f71):
    v = voice_view.build(run(f71, CLEAN), f71)
    assert v["spotlight"]["stats"] == [{"value": 15, "label": "PTS"}, {"value": 11, "label": "REB"},
                                       {"value": 12, "label": "AST"}]
    assert v["spotlight"]["initials"] == "AT" and v["spotlight"]["team"] == "Phoenix Mercury"
