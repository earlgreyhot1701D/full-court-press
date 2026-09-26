"""Task 3.2: voice_client, with a fake Bedrock client. No network, no AWS."""
import json

import pytest

from zine import voice_client, voice_run
from test_fact_lock import CLEAN
from test_facts_gotn import golden_facts, needs_golden


class FakeBedrock:
    def __init__(self, text):
        self.text, self.calls = text, []

    def converse(self, **kw):
        self.calls.append(kw)
        return {"output": {"message": {"role": "assistant", "content": [{"text": self.text}]}}}


@pytest.mark.parametrize("text, ok", [
    (json.dumps(CLEAN), True),
    ("```json\n" + json.dumps(CLEAN) + "\n```", True),
    ("Here you go: " + json.dumps(CLEAN), True),
    ("no json here", False),
    ("[1, 2, 3]", False),
    ('{"headline": ', False),
])
def test_parse(text, ok):
    assert (voice_client.parse(text) == CLEAN) is ok


def test_write_sends_exactly_what_it_was_given(monkeypatch):
    monkeypatch.setenv("MODEL_ID", "test-profile")
    fake = FakeBedrock(json.dumps(CLEAN))
    msgs = [{"role": "user", "content": [{"text": "EDITION: PHX\nFACTS:\n{}"}]}]
    assert voice_client.write("SYSTEM", msgs, client=fake) == CLEAN
    kw = fake.calls[0]
    assert kw["modelId"] == "test-profile" and kw["system"] == [{"text": "SYSTEM"}]
    assert kw["messages"] == msgs and kw["inferenceConfig"]["maxTokens"] == voice_client.MAX_TOKENS


@needs_golden
def test_full_flow_with_fake_bedrock(monkeypatch):
    monkeypatch.setenv("MODEL_ID", "test-profile")
    fake = FakeBedrock(json.dumps(CLEAN))
    f = golden_facts()["25071"]
    r = voice_run.run(lambda s, m: voice_client.write(s, m, client=fake), f, "the_call", "PHX")
    assert r["calls"] == 1 and r["sections"]["headline"] == CLEAN["headline"]
    sent = fake.calls[0]["messages"][0]["content"][0]["text"]
    assert sent.startswith("EDITION: PHX\nFACTS:\n")
