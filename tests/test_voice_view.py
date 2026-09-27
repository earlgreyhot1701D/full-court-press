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
    from zine import site_build
    rows = [site_build.slate_row(f, f["game_id"])]
    results = {(edition, voice): result}
    files = site_build.issue_files(f, results, f["game_id"], rows)
    return files[voice_view.issue_path(f, edition, voice)][0].decode("utf-8")


def run(f, *answers, voice="the_call"):
    q = [copy.deepcopy(a) for a in answers]
    return voice_run.run(lambda s, m: q.pop(0), f, voice, "PHX")


@needs_golden
def test_urls_default_voice_is_the_call(f71):
    assert voice_view.issue_path(f71, "PHX", "the_call") == "wnba/2026-09-21/25071/PHX/index.html"
    assert voice_view.issue_path(f71, "PHX", "film_room") == "wnba/2026-09-21/25071/PHX/film-room/index.html"
    assert voice_view.issue_path(f71, "PHX", prefix="golden/") == "golden/wnba/2026-09-21/25071/PHX/index.html"
    links = voice_view.voice_links(f71, "PHX", "film_room")
    assert [l["label"] for l in links] == ["The Call", "The Film Room"]
    assert links[0]["url"] == "../../../../../wnba/2026-09-21/25071/PHX/index.html" and links[1]["current"]


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
    assert "The writers&rsquo; room passed on this one" in html
    assert CLEAN["headline"] in html and "33 points" not in html
    # the floor: a code-written recap, labeled as such, instead of an empty story
    assert 'class="recap plainrecap">The Mercury beat the Wings 87-86.' in html
    assert "written by code, from the counted facts . no AI" in html


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
    assert "The writers&rsquo; room passed on this one" in html and "Spotlight" not in html
    assert 'class="recap plainrecap"' in html


@needs_golden
def test_spotlight_stats_come_from_facts_not_the_model(f71):
    v = voice_view.build(run(f71, CLEAN), f71)
    assert v["spotlight"]["stats"] == [{"value": 15, "label": "PTS"}, {"value": 11, "label": "REB"},
                                       {"value": 12, "label": "AST"}]
    assert v["spotlight"]["initials"] == "AT" and v["spotlight"]["team"] == "Phoenix Mercury"


@needs_golden
def test_plain_recap_passes_the_fact_lock_for_every_golden_page():
    """The code-written recap is true by construction; prove it with the same lock the AI faces."""
    from zine import dev_render_golden, fact_lock, plain_recap
    for f in dev_render_golden.load_all():
        phrases = set(f.get("allowed_names", [])) | fact_lock.COMMON_CAPS
        for t in (f["home"], f["away"]):
            text = plain_recap.build(f, t["abbrev"])
            assert text, (f["game_id"], t["abbrev"])
            assert fact_lock._check_text(text, set(f.get("allowed_numbers", [])), phrases) == "ok", (f["game_id"], t["abbrev"], text)
            if t["abbrev"] == f["winner_abbrev"]:
                assert " beat " in text.split(".")[0]
            else:
                assert " lost to " in text.split(".")[0]


@needs_golden
def test_cards_and_featured_game_follow_the_voice_that_kept_its_recap(f71):
    from zine import site_build
    from zine.game_of_night import pick
    kept = run(f71, CLEAN, voice="film_room")
    results = {("PHX", "the_call"): None, ("PHX", "film_room"): kept}
    row = site_build.slate_row(f71, f71["game_id"], results=results)
    assert row["read"].endswith("PHX/film-room/index.html")
    assert site_build.featurable([f71], {f71["game_id"]: results}) == {f71["game_id"]}
    assert site_build.featurable([f71], {f71["game_id"]: {}}) == set()
    # nothing qualifies: every game stays in the running
    assert pick([f71], eligible=set()) == f71["game_id"]


def test_pick_skips_a_game_whose_winner_page_lost_its_recap():
    from zine.game_of_night import pick
    close = {"game_id": 1, "final_margin": 1, "tip_time_utc": "2026-09-24T23:00Z", "notable": []}
    blowout = {"game_id": 2, "final_margin": 30, "tip_time_utc": "2026-09-24T23:30Z", "notable": []}
    assert pick([close, blowout]) == 1
    assert pick([close, blowout], eligible={2}) == 2
