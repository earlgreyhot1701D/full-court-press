"""Block 3 step 2: voices, the banned-word check, and the retry-once-then-drop flow, run against
a fake model. The fake plants a wrong number, a banned word, broken JSON, and a crash."""
import copy
import json

import pytest

from zine import voice_run, voices
from test_fact_lock import CLEAN, with_
from test_facts_gotn import golden_facts, needs_golden


@pytest.fixture(scope="module")
def f71():
    return golden_facts()["25071"]


class Fake:
    """Returns the queued answers in order and records what it was sent."""

    def __init__(self, *answers):
        self.answers, self.sent = list(answers), []

    def __call__(self, system, messages):
        self.sent.append((system, messages))
        a = self.answers.pop(0)
        if isinstance(a, Exception):
            raise a
        return copy.deepcopy(a)


PLANTED = with_("recap", "Kahleah Copper scored 33 points as Phoenix beat Dallas 87-86.")


# ---- the flow ----

@needs_golden
def test_clean_first_try_is_one_call(f71):
    fake = Fake(CLEAN)
    r = voice_run.run(fake, f71, "the_call", "PHX")
    assert r["calls"] == 1 and all(v is not None for v in r["sections"].values())
    assert r["sections"]["the_number"] == "kahleah_copper_pts"


@needs_golden
def test_planted_bad_number_is_caught_and_retried(f71):
    fake = Fake(PLANTED, CLEAN)
    r = voice_run.run(fake, f71, "the_call", "PHX")
    assert r["calls"] == 2
    assert r["sections"]["recap"] == CLEAN["recap"]  # the retry's recap, not the planted one
    retry_text = fake.sent[1][1][0]["content"][0]["text"]
    assert "REJECTED" in retry_text and "33" in retry_text and "recap" in retry_text


@needs_golden
def test_planted_bad_number_twice_drops_only_the_recap(f71):
    r = voice_run.run(Fake(PLANTED, PLANTED), f71, "the_call", "PHX")
    s = r["sections"]
    assert s["recap"] is None
    assert s["headline"] == CLEAN["headline"] and s["spotlight"] == CLEAN["spotlight"]
    assert "33" not in json.dumps(s)


@needs_golden
def test_banned_word_is_caught(f71):
    bad = with_("spotlight.text", "Thomas played through a sore ankle: 15 points, 11 rebounds, 12 assists.")
    r = voice_run.run(Fake(bad, bad), f71, "film_room", "PHX")
    assert r["sections"]["spotlight"] is None
    assert r["log"][0]["sections"]["spotlight"] == {"rule": "banned"}


@needs_golden
def test_scheme_words_banned_for_film_room_only(f71):
    text = "Dallas went zone late and Phoenix found Copper anyway."
    assert voices.banned_hit(text, "film_room") == "zone"
    assert voices.banned_hit(text, "the_call") is None


@needs_golden
@pytest.mark.parametrize("first", [None, "not json", RuntimeError("timeout"), dict(CLEAN, extra="x")])
def test_bad_first_answer_counts_as_failure_and_retries(f71, first):
    r = voice_run.run(Fake(first, CLEAN), f71, "the_call", "DAL")
    assert r["calls"] == 2 and r["sections"]["headline"] == CLEAN["headline"]


@needs_golden
def test_crash_twice_drops_everything_and_logs_only_the_error_type(f71):
    r = voice_run.run(Fake(RuntimeError("secret body text"), RuntimeError("x")), f71, "the_call", "DAL")
    assert all(v is None for v in r["sections"].values())
    assert r["log"][0]["error"] == "RuntimeError" and "secret" not in json.dumps(r["log"])


@needs_golden
def test_attempts_are_never_mixed(f71):
    # attempt 1: headline bad, rest fine (3 ok). attempt 2: recap bad, rest fine (3 ok). tie -> retry wins whole
    a1 = with_("headline", "Copper drops 44 in Dallas")
    a2 = with_("recap", "Copper scored 44.")
    r = voice_run.run(Fake(a1, a2), f71, "the_call", "PHX")
    assert r["sections"]["headline"] == CLEAN["headline"] and r["sections"]["recap"] is None


@needs_golden
def test_better_first_attempt_is_kept(f71):
    a2 = dict(with_("recap", "Copper scored 44."), headline="Copper drops 44")
    r = voice_run.run(Fake(PLANTED, a2), f71, "the_call", "PHX")
    assert r["sections"]["headline"] == CLEAN["headline"] and r["sections"]["recap"] is None


@needs_golden
def test_call_budget_stops_calls(f71):
    b = voice_run.CallBudget(1)
    fake = Fake(PLANTED, CLEAN)
    r = voice_run.run(fake, f71, "the_call", "PHX", budget=b)
    assert len(fake.sent) == 1 and r["sections"]["recap"] is None
    r2 = voice_run.run(Fake(CLEAN), f71, "film_room", "PHX", budget=b)
    assert r2["calls"] == 0 and all(v is None for v in r2["sections"].values())


@needs_golden
def test_log_never_carries_model_text(f71):
    r = voice_run.run(Fake(PLANTED, PLANTED), f71, "the_call", "PHX")
    assert "33" not in json.dumps(r["log"]) and "Copper" not in json.dumps(r["log"])


# ---- the prompts ----

@needs_golden
def test_user_message_is_only_edition_and_facts(f71):
    msg = voices.user_message(f71, "PHX")
    head, body = msg.split("\nFACTS:\n", 1)
    assert head == "EDITION: PHX" and json.loads(body) == json.loads(json.dumps(f71))


@pytest.mark.parametrize("voice", voices.VOICE_ORDER)
def test_system_prompt_has_the_rules(voice):
    p = voices.system_prompt(voice)
    for must in (voices.VOICES[voice]["label"], "sentence case", "the_number_key", "NEVER",
                 "Use only numbers and names that appear in FACTS", "dropped_categories",
                 "Never do your own math", "plain_facts", "Never credit a run to one player",
                 "standings movement", "Never blame a player"):
        assert must in p
    assert "—" not in p.replace('"—"', "")


def test_banned_is_whole_word():
    assert voices.banned_hit("Phoenix had the lockdown answer and spread the floor.", "the_call") is None
    assert voices.banned_hit("A body of work.", "the_call") == "body"
    assert voices.banned_hit("Wings — gone.", "the_call") == "—"
    assert voices.banned_hit("the 3-pointers fell", "the_call") == "3-pointers"
