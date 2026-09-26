"""Block 5b.1 and 5b.2: audio script (code only, 30 words max) and the Polly client (neural only)."""
import io

import pytest

from zine import audio_client, audio_script
from test_facts_gotn import golden_facts, needs_golden


@needs_golden
def test_script_is_code_built_and_short():
    F = golden_facts()
    s = audio_script.build(F["25014"], "Fever storm back from 10 down to stun Dream in overtime")
    assert s.startswith("Indiana Fever 95, Atlanta Dream 91, in overtime.")
    assert s.endswith("Allisha Gray led everyone with 32 points.")
    assert len(s.split()) <= 30
    assert "overtime" not in audio_script.build(F["25071"]).split(".")[0]


@needs_golden
def test_long_headline_is_dropped_before_the_score():
    f = golden_facts()["25071"]
    s = audio_script.build(f, " ".join(["word"] * 40))
    assert s == "Phoenix Mercury 87, Dallas Wings 86." or len(s.split()) <= 30
    assert s.startswith("Phoenix Mercury 87, Dallas Wings 86.")


class FakePolly:
    def __init__(self, fail=False):
        self.fail, self.kw = fail, None

    def synthesize_speech(self, **kw):
        self.kw = kw
        if self.fail:
            raise RuntimeError("throttled")
        return {"AudioStream": io.BytesIO(b"ID3mp3")}


def test_speak_uses_neural_and_returns_bytes(monkeypatch):
    monkeypatch.delenv("POLLY_ENGINE", raising=False)
    p = FakePolly()
    assert audio_client.speak("Hello.", client=p) == b"ID3mp3"
    assert p.kw["Engine"] == "neural" and p.kw["OutputFormat"] == "mp3" and p.kw["TextType"] == "text"


def test_speak_failure_returns_none():
    assert audio_client.speak("Hello.", client=FakePolly(fail=True)) is None


def test_generative_engine_is_refused(monkeypatch):
    monkeypatch.setenv("POLLY_ENGINE", "generative")
    with pytest.raises(ValueError):
        audio_client.speak("Hello.", client=FakePolly())
