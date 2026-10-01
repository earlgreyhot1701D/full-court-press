"""Every bad sentence we paid for once, kept as a permanent test.

Each one is a recap the AI wrote (or one Claude wrote by hand while testing the checks), from the
audits logged in LEDGER.md and the article. Two kinds:

  CAUGHT  the checks cut it today. If a change ever lets it through, this file fails.
  LIMIT   the checks let it through today: every number in it is a correct fact, and the sentence
          around them is wrong. That is the documented limit of the fact lock. These are marked
          xfail(strict=True), so the suite stays green while the limit stands, and goes red the day
          something starts catching them, so the README and article claims get updated with it.
"""
import copy

import pytest

from zine import voice_run
from test_fact_lock import CLEAN
from test_facts_gotn import golden_facts, needs_golden


def recap_verdict(game_id, sentence):
    """The recap section's result from the same check the morning run uses (lock + banned words)."""
    out = copy.deepcopy(CLEAN)
    out["recap"] = sentence
    res = voice_run.check(out, golden_facts()[game_id], "the_call")
    return res["sections"]["recap"]


CAUGHT = [
    # (game, sentence, rule that should fire, where it came from)
    ("25071", "Kahleah Copper scored 33 points as Phoenix edged Dallas.", "number",
     "golden test: a number that is not in the facts (Copper had 31)"),
    ("25071", "Kahleah Copper poured in twenty-six for Phoenix.", "spelled_number",
     "spelled-out numbers can't sneak past the number check"),
    ("25014", "The Dream stay perfect in the East after a 30-14 start.", "banned",
     "live audit Sep 26: an invented record ('perfect') on a team at 30-14"),
    ("25071", "The Mercury climbed past Dallas in the West with the win.", "banned",
     "live audit Sep 26: standings movement the facts don't track"),
    ("25071", "Kahleah Copper went 10 for 10 at the line in the fourth.", "banned_split",
     "shooting splits: the facts have made shots, never attempts"),
    ("25071", "Copper's dagger sank Dallas 87-86.", "banned",
     "voice samples: a specific moment the facts don't contain"),
]


@needs_golden
@pytest.mark.parametrize("game_id,sentence,rule,origin", CAUGHT, ids=[c[3][:40] for c in CAUGHT])
def test_caught_failures_stay_caught(game_id, sentence, rule, origin):
    verdict = recap_verdict(game_id, sentence)
    assert verdict != "ok", "regression: this sentence now passes the checks (%s)" % origin
    assert rule.split("_")[0] in verdict["rule"], (verdict, origin)


LIMITS = [
    ("25014", "The fourth quarter belonged to Atlanta.",
     "golden audit: Indiana won the 4th 17-9; no number in the sentence to check"),
    ("25014", "Atlanta built a 28-9 lead before Indiana came back.",
     "golden audit: Atlanta's 28 in the 3rd and 9 in the 4th, mashed into a lead that never existed"),
    ("25071", "Copper split her 31 right down the middle: 10 field goals, 10 free throws.",
     "voice samples: 10 field goals is at least 20 points; every number is a correct fact"),
]


@needs_golden
@pytest.mark.xfail(strict=True, reason="known limit of the fact lock: correct numbers, wrong claim")
@pytest.mark.parametrize("game_id,sentence,origin", LIMITS, ids=[c[2][:40] for c in LIMITS])
def test_known_limits_still_get_through(game_id, sentence, origin):
    assert recap_verdict(game_id, sentence) != "ok", origin


@needs_golden
def test_clean_recap_still_passes():
    """Guard for the guard: the checks must not cut a correct recap."""
    assert recap_verdict("25071", CLEAN["recap"]) == "ok"
