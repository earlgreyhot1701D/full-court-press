"""The exact shape a voice must return. Pure: no network, no model.

Anything that does not match is discarded before the fact lock sees it. Extra keys are
invalid, at the top level and inside `spotlight`, so no field ever reaches a page unchecked.
"""

LIMITS = {"headline": 90, "recap": 900, "spotlight.text": 300}
TOP_KEYS = {"headline", "recap", "spotlight", "the_number_key"}
SPOTLIGHT_KEYS = {"player", "text"}


def _text(value, name, limit, errors):
    if not isinstance(value, str):
        errors.append("%s must be text" % name)
    elif not value.strip():
        errors.append("%s is empty" % name)
    elif limit and len(value) > limit:
        errors.append("%s is %d characters, limit %d" % (name, len(value), limit))


def errors(out):
    """Every reason `out` fails the schema, in plain words. Empty list means valid.
    The reasons name fields and limits only, never the model's text, so they are safe to log."""
    if not isinstance(out, dict):
        return ["response is not a JSON object"]
    errs = []
    for k in sorted(TOP_KEYS - out.keys()):
        errs.append("missing key: %s" % k)
    for k in sorted(out.keys() - TOP_KEYS, key=str):
        errs.append("extra key: %s" % k)
    if "headline" in out:
        _text(out["headline"], "headline", LIMITS["headline"], errs)
    if "recap" in out:
        _text(out["recap"], "recap", LIMITS["recap"], errs)
    if "the_number_key" in out:
        _text(out["the_number_key"], "the_number_key", None, errs)
    if "spotlight" in out:
        sp = out["spotlight"]
        if not isinstance(sp, dict):
            errs.append("spotlight must be an object")
        else:
            for k in sorted(SPOTLIGHT_KEYS - sp.keys()):
                errs.append("missing key: spotlight.%s" % k)
            for k in sorted(sp.keys() - SPOTLIGHT_KEYS, key=str):
                errs.append("extra key: spotlight.%s" % k)
            if "player" in sp:
                _text(sp["player"], "spotlight.player", None, errs)
            if "text" in sp:
                _text(sp["text"], "spotlight.text", LIMITS["spotlight.text"], errs)
    return errs


def validate(out):
    """`out` unchanged if it matches the schema, else None."""
    return out if not errors(out) else None
