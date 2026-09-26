"""One voice, one edition: write, check, retry once, then keep or drop each section. Pure: the
model call is passed in as `write`, so this runs offline against a fake.

write(system, messages) -> dict | None
    `messages` is Bedrock Converse shape: [{"role": "user", "content": [{"text": ...}]}].
    Returns the parsed JSON object, or None if the call failed or the reply was not JSON.
    voice_client.write is the real one (Kiro, Block 3.2).

Rules (design.md, Error handling):
- A schema failure or a failed call counts as a lock failure: retry once, then drop.
- The retry is one fresh user message: the same facts plus a note naming what failed. Nothing the
  model wrote is sent back except the failing token inside that note.
- Sections are never mixed across attempts, so a headline and recap always come from the same
  answer. The attempt that passes more sections wins; on a tie, the retry wins.
- A section that fails its check is dropped (None), and the page shows "the writers' room passed".
- Logs get `log_safe` results only: rules, never model text.
"""
from zine import fact_lock, voices

TEXT_FIELDS = {"headline": ("headline",), "recap": ("recap",), "spotlight": ("spotlight", "text")}


class CallBudget:
    """MAX_MODEL_CALLS_PER_RUN, shared across every voice and edition in one run."""

    def __init__(self, max_calls):
        self.left = max_calls

    def take(self):
        if self.left <= 0:
            return False
        self.left -= 1
        return True


def _field(out, path):
    v = out
    for p in path:
        v = v[p]
    return v


def check(out, facts, voice):
    """fact_lock.check plus the banned-word check on each text section."""
    res = fact_lock.check(out, facts)
    for section, path in TEXT_FIELDS.items():
        if res["sections"][section] == "ok":
            hit = voices.banned_hit(_field(out, path), voice)
            if hit:
                res["sections"][section] = {"rule": "banned", "token": hit}
    res["ok"] = all(v == "ok" for v in res["sections"].values())
    return res


def _call(write, system, text, budget):
    if budget is not None and not budget.take():
        return None, "budget"
    try:
        return write(system, [{"role": "user", "content": [{"text": text}]}]), None
    except Exception as e:  # never let one voice take down the run; log the type, not the text
        return None, type(e).__name__


def _sections(out, res):
    keep = {}
    for s in fact_lock.SECTIONS:
        ok = res["sections"][s] == "ok"
        if s == "the_number":
            keep[s] = out["the_number_key"] if ok else None
        else:
            keep[s] = out[s] if ok else None
    return keep


def run(write, facts, voice, edition, budget=None):
    """-> {"voice", "edition", "sections": {headline, recap, spotlight, the_number}, "calls", "log"}
    A section value of None means dropped."""
    system = voices.system_prompt(voice)
    user = voices.user_message(facts, edition)
    log, attempts = [], []

    for attempt in (1, 2):
        text = user if attempt == 1 else user + "\n\nYOUR LAST ANSWER WAS REJECTED. " + note
        out, err = _call(write, system, text, budget)
        if err == "budget":
            log.append({"attempt": attempt, "skipped": "call budget reached"})
            break
        res = check(out, facts, voice)
        entry = {"attempt": attempt, **fact_lock.log_safe(res)}
        if err:
            entry["error"] = err
        log.append(entry)
        attempts.append((out, res))
        if res["ok"]:
            break
        note = fact_lock.retry_note(res)

    best = None
    for out, res in attempts:  # later attempt wins ties
        n = sum(v == "ok" for v in res["sections"].values())
        if best is None or n >= best[0]:
            best = (n, out, res)
    if best is None or best[0] == 0:
        sections = {s: None for s in fact_lock.SECTIONS}
    else:
        sections = _sections(best[1], best[2])
    return {"voice": voice, "edition": edition, "sections": sections,
            "calls": len(attempts), "log": log}


def recheck(result, facts):
    """Re-apply today's rules to a saved result, section by section, with no model call. A section
    that breaks a rule added after it was written is dropped. Used at every render, so a rule change
    reaches pages already published the next time they are rebuilt."""
    if not result:
        return result
    voice, s = result["voice"], dict(result["sections"])
    allowed = set(facts.get("allowed_numbers", []))
    phrases = set(facts.get("allowed_names", [])) | fact_lock.COMMON_CAPS
    players = {l["player"] for l in facts.get("player_lines", [])}
    for key in ("headline", "recap"):
        if s.get(key) and (fact_lock._check_text(s[key], allowed, phrases) != "ok" or voices.banned_hit(s[key], voice)):
            s[key] = None
    sp = s.get("spotlight")
    if sp and (sp.get("player") not in players or fact_lock._check_text(sp.get("text", ""), allowed, phrases) != "ok"
               or voices.banned_hit(sp.get("text", ""), voice)):
        s["spotlight"] = None
    if s.get("the_number") and (s["the_number"] not in facts.get("numbers", {})
                                or s["the_number"] not in facts.get("number_labels", {})):
        s["the_number"] = None
    return dict(result, sections=s)
