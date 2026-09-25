"""Tasks 3.1 and 3.4: the output schema and the fact lock (design.md, Testing), on the real
facts sheet for game 25071 and on every golden game."""
import copy

import pytest

from zine import fact_lock, output_schema
from test_facts_gotn import golden_facts, needs_golden


@pytest.fixture(scope="module")
def facts_all():
    return golden_facts()


@pytest.fixture(scope="module")
def f71(facts_all):
    return facts_all["25071"]


CLEAN = {
    "headline": "Mercury hold on by 1 in Dallas",
    "recap": ("Phoenix beat Dallas 87-86. Kahleah Copper scored 31 points, and Alyssa Thomas put up "
              "15 points, 11 rebounds and 12 assists. It was one of those nights for the Mercury, "
              "and a Game of the Night."),
    "spotlight": {"player": "Alyssa Thomas",
                  "text": "Thomas's triple-double did the quiet work: 15 points, 11 rebounds, 12 assists."},
    "the_number_key": "kahleah_copper_pts",
}


def with_(field, value):
    out = copy.deepcopy(CLEAN)
    if field.startswith("spotlight."):
        out["spotlight"][field.split(".")[1]] = value
    else:
        out[field] = value
    return out


def failed(res, section):
    v = res["sections"][section]
    return None if v == "ok" else (v["rule"], v["token"])


# ---- output_schema ----

def test_schema_accepts_clean():
    assert output_schema.validate(CLEAN) is CLEAN


@pytest.mark.parametrize("bad, why", [
    (dict(CLEAN, extra="x"), "extra key: extra"),
    (with_("spotlight.photo", "x"), "extra key: spotlight.photo"),
    ({k: v for k, v in CLEAN.items() if k != "recap"}, "missing key: recap"),
    (with_("headline", "x" * 91), "headline is 91 characters, limit 90"),
    (with_("recap", "x" * 901), "recap is 901 characters, limit 900"),
    (with_("spotlight.text", "x" * 301), "spotlight.text is 301 characters, limit 300"),
    (with_("headline", "   "), "headline is empty"),
    (with_("the_number_key", 31), "the_number_key must be text"),
    (with_("spotlight", "Alyssa Thomas"), "spotlight must be an object"),
    ("not json", "response is not a JSON object"),
    (None, "response is not a JSON object"),
])
def test_schema_rejects(bad, why):
    assert output_schema.validate(bad) is None
    assert why in output_schema.errors(bad)


# ---- fact_lock, design.md Testing list ----

@needs_golden
def test_clean_output_passes(f71):
    res = fact_lock.check(CLEAN, f71)
    assert res["ok"], res


@needs_golden
def test_planted_wrong_number_fails(f71):
    res = fact_lock.check(with_("recap", "Kahleah Copper scored 33 points."), f71)
    assert not res["ok"]
    assert failed(res, "recap") == ("number", "33")
    assert failed(res, "headline") is None  # one bad section does not take the others with it


@needs_golden
def test_spelled_number_fails(f71):
    res = fact_lock.check(with_("headline", "Copper drops twenty-six in Dallas"), f71)
    assert failed(res, "headline") == ("spelled_number", "twenty")


@needs_golden
def test_unknown_name_fails_mid_sentence(f71):
    res = fact_lock.check(with_("recap", "Phoenix leaned on Caitlin Clark late."), f71)
    assert failed(res, "recap") == ("name", "Caitlin Clark")


@needs_golden
def test_bad_number_key_fails(f71):
    res = fact_lock.check(with_("the_number_key", "copper_threes"), f71)
    assert failed(res, "the_number") == ("the_number_key", "copper_threes")


# ---- known edges ----

@needs_golden
def test_unknown_name_at_sentence_start_fails(f71):
    # the design's first draft skipped sentence starts; that would let this through
    res = fact_lock.check(with_("recap", "Diana Taurasi watched from the stands."), f71)
    assert failed(res, "recap") == ("name", "Diana Taurasi")


@needs_golden
@pytest.mark.parametrize("text", ["Stewart was not needed.", "Dallas had no answer for Stewart."])
def test_lone_surname_not_in_game_fails(f71, text):
    assert failed(fact_lock.check(with_("recap", text), f71), "recap") == ("name", "Stewart")


@needs_golden
@pytest.mark.parametrize("text", [
    "After the break, Phoenix pulled away.",
    "Down the stretch, Thomas's passing decided it.",
    "The Mercury won the West matchup on a Sunday.",
    "It was no one's night but Copper's.",
    "Phoenix got one more stop.",
])
def test_ordinary_sentences_pass(f71, text):
    assert fact_lock.check(with_("recap", text), f71)["ok"]


@needs_golden
@pytest.mark.parametrize("text, rule, token", [
    ("A one-point game in Dallas.", "spelled_number", "one"),
    ("Copper hit the go-ahead shot with 4:07 left.", "number", "07"),
    ("Dallas shot 45% from the floor.", "number", "45"),
    ("A dozen lead changes.", "spelled_number", "dozen"),
])
def test_edges_fail(f71, text, rule, token):
    assert failed(fact_lock.check(with_("recap", text), f71), "recap") == (rule, token)


@needs_golden
def test_title_case_headline_fails(f71):
    # documented behavior: the prompt asks for sentence case; Title Case reads as names
    res = fact_lock.check(with_("headline", "Mercury Survive Wings In Thriller"), f71)
    assert failed(res, "headline") == ("name", "Mercury Survive Wings In Thriller")


@needs_golden
@pytest.mark.parametrize("player", ["Phoenix Mercury", "Thomas", "Caitlin Clark"])
def test_spotlight_player_must_be_full_name_on_stat_line(f71, player):
    assert failed(fact_lock.check(with_("spotlight.player", player), f71), "spotlight")[0] == "spotlight_player"


@needs_golden
def test_schema_failure_fails_every_section(f71):
    res = fact_lock.check(dict(CLEAN, extra="x"), f71)
    assert not res["ok"] and all(v["rule"] == "schema" for v in res["sections"].values())


# ---- every real name on the golden set passes (no false rejects on real players) ----

@needs_golden
def test_every_golden_name_and_score_passes(facts_all):
    # every player on every golden stat line, by full name, in batches under the recap limit
    for gid, f in facts_all.items():
        players = [l["player"] for l in f["player_lines"]]
        w, l = (f["home"], f["away"]) if f["winner_abbrev"] == f["home"]["abbrev"] else (f["away"], f["home"])
        score = "%s beat %s %d-%d." % (w["team"], l["team"], w["score"], l["score"])
        for i in range(0, len(players), 8):
            out = {"headline": "%s win" % w["team"],
                   "recap": " ".join("%s played." % p for p in players[i:i + 8]),
                   "spotlight": {"player": players[i], "text": score},
                   "the_number_key": f["the_number_key"]}
            res = fact_lock.check(out, f)
            assert res["ok"], (gid, res)


@needs_golden
def test_hyphenated_sentence_start_word_passes(f71):
    assert fact_lock.check(with_("recap", "Triple-double for Thomas."), f71)["ok"]


# ---- logging and retry ----

@needs_golden
def test_log_safe_drops_model_tokens(f71):
    res = fact_lock.check(with_("recap", "Phoenix leaned on Caitlin Clark late."), f71)
    safe = fact_lock.log_safe(res)
    assert "Caitlin" not in repr(safe) and safe["sections"]["recap"] == {"rule": "name"}


@needs_golden
def test_retry_note_names_section_and_token(f71):
    res = fact_lock.check(with_("recap", "Kahleah Copper scored 33 points."), f71)
    note = fact_lock.retry_note(res)
    assert "recap" in note and "33" in note and "headline" not in note
    assert fact_lock.retry_note(fact_lock.check(CLEAN, f71)) == ""
