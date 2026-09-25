"""The fact lock: a voice may only use numbers and names that are in the facts sheet.
Pure: no network, no model.

check(out, facts) -> {"ok": bool, "sections": {section: "ok" | {"rule": ..., "token": ...}}}

Sections: headline, recap, spotlight (player and text), the_number (the key only; the value on
the page always comes from the facts sheet, never from the model).

Rules, from design.md:
1. Numbers. Every run of digits in a text field must be in `allowed_numbers`. "9-17" and "45%"
   split into their digits by the regex, so each part is checked on its own.
2. Spelled numbers. A fixed list of number words rejects the section. "one" is allowed only
   inside "one of", "no one", "one more".
3. Names. Every capitalized word must be covered by a name in `allowed_names` or a phrase in
   COMMON_CAPS. Runs of capitalized words are matched longest-first, so "Alyssa Thomas" is
   checked as one name. The first word of a sentence is capitalized for grammar, so it is also
   covered if it is an ordinary word in SENTENCE_STARTERS. Nothing else is skipped: a name at
   the start of a sentence is checked like any other.
4. `spotlight.player` must be a full name from this game's stat line (not a team, not a surname).
5. `the_number_key` must be a key in `numbers`.

What the lock does NOT prove, stated so nobody reads more into a pass than is there:
- That a number is attached to the right claim. "Copper had 12 rebounds" passes if 12 is any
  number in the game. Small numbers (0 to 12 or so) are almost always somewhere in a stat line.
- That a spelled ordinal is right. "the third quarter" is not checked.
- That we counted right. That is pbp_stats and its gates, not this module.

Reasons carry the offending token for the retry message sent back to the model. The token is a
fragment of model output, so it never goes to a log: log with `log_safe(result)`.
"""
import re

from zine.output_schema import errors as schema_errors

SECTIONS = ("headline", "recap", "spotlight", "the_number")

_NUMBER = re.compile(r"\d+(?:\.\d+)?")

SPELLED = ("zero one two three four five six seven eight nine ten eleven twelve thirteen "
           "fourteen fifteen sixteen seventeen eighteen nineteen twenty thirty forty fifty "
           "sixty seventy eighty ninety hundred thousand dozen").split()
_SPELLED = re.compile(r"\b(%s)\b" % "|".join(SPELLED), re.IGNORECASE)
_ONE_OK = re.compile(r"\b(one of|no one|one more)\b", re.IGNORECASE)

# Capitalized words a voice may use that are not names from the game.
COMMON_CAPS = {
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday",
    "January", "February", "March", "April", "May", "June", "July", "August", "September",
    "October", "November", "December",
    "The Call", "The Film Room", "Film Room", "The Number", "Full Court Press",
    "WNBA", "OT", "East", "West", "Eastern Conference", "Western Conference", "I",
}
# Capitalized phrases with lowercase words inside. Lowercased before the name scan.
COMMON_PHRASES = ("Game of the Night",)

# Ordinary words that are capitalized only because they start a sentence.
SENTENCE_STARTERS = set("""
a an the it its in on at after before when with without but and or nor then that this these
those there their her his she he they them we you our your both every each no not nobody
nothing everything everyone someone somebody down up late early by for from over through
across behind ahead still yet so now once twice what who how why where watch look call credit
give put back tied trailing leading facing coming final first second third fourth fifth
overtime game triple double halftime just only even meanwhile also another all some most few
many if as while until since because although though here home road defense offense
rebounding shooting balance big small short long clutch plenty enough too again instead maybe
sure yes chalk let make take keep turn hold win wins loss losses lost won close closing opening
free steady quiet loud wild ugly pretty tough hard easy fast slow good bad great best worst
next last tonight tomorrow yesterday morning night one more to of into out off near far such
whatever whoever anyone nobody none neither either than more less much very really almost
""".split())

# A word keeps inner apostrophes and hyphens, so "A'ja" and "Te-Hina" stay one name.
_WORD = re.compile(r"(?<![\w'\u2019-])[^\W\d_](?:[^\W_]|['\u2019-](?=[^\W_]))*")
_STARTS_SENTENCE = set(".!?:;\"“”(\n")


def _token(word):
    """Drop a possessive: "Thomas's" -> "Thomas"."""
    for s in ("'s", "’s"):
        if word.endswith(s):
            return word[:-2]
    return word


def _cap_groups(text):
    """Runs of capitalized words separated only by spaces, with whether the run starts a sentence."""
    for p in COMMON_PHRASES:
        text = text.replace(p, p.lower())
    groups, cur, last_end = [], [], None
    for m in _WORD.finditer(text):
        w = m.group()
        if not w[0].isupper():
            if cur:
                groups.append(cur)
            cur, last_end = [], m.end()
            continue
        joined = cur and text[last_end:m.start()].strip(" ") == ""
        if not joined:
            if cur:
                groups.append(cur)
            before = text[:m.start()].rstrip(" \t")
            cur = [(bool(not before or before[-1] in _STARTS_SENTENCE), None)]
        cur.append(_token(w))
        last_end = m.end()
    if cur:
        groups.append(cur)
    return [(g[0][0], g[1:]) for g in groups if len(g) > 1]


def _uncovered_name(text, phrases):
    """The first capitalized run that is not fully covered, or None."""
    for at_start, words in _cap_groups(text):
        i = 0
        while i < len(words):
            for j in range(len(words), i, -1):
                if " ".join(words[i:j]) in phrases:
                    i = j
                    break
            else:
                if i == 0 and at_start and words[0].split("-")[0].lower() in SENTENCE_STARTERS:
                    i = 1
                else:
                    return " ".join(words)
    return None


def _check_text(text, allowed_numbers, phrases):
    for m in _NUMBER.finditer(text):
        if m.group() not in allowed_numbers:
            return {"rule": "number", "token": m.group()}
    ok_spans = [m.span() for m in _ONE_OK.finditer(text)]
    for m in _SPELLED.finditer(text):
        if m.group().lower() == "one" and any(a <= m.start() and m.end() <= b for a, b in ok_spans):
            continue
        return {"rule": "spelled_number", "token": m.group()}
    name = _uncovered_name(text, phrases)
    if name:
        return {"rule": "name", "token": name}
    return "ok"


def check(out, facts):
    if schema_errors(out):
        bad = {"rule": "schema", "token": None}
        return {"ok": False, "sections": {s: bad for s in SECTIONS}}
    allowed_numbers = set(facts.get("allowed_numbers", []))
    phrases = set(facts.get("allowed_names", [])) | COMMON_CAPS
    players = {l["player"] for l in facts.get("player_lines", [])}

    sections = {
        "headline": _check_text(out["headline"], allowed_numbers, phrases),
        "recap": _check_text(out["recap"], allowed_numbers, phrases),
    }
    sp = out["spotlight"]
    if sp["player"] not in players:
        sections["spotlight"] = {"rule": "spotlight_player", "token": sp["player"]}
    else:
        sections["spotlight"] = _check_text(sp["text"], allowed_numbers, phrases)
    if out["the_number_key"] in facts.get("numbers", {}):
        sections["the_number"] = "ok"
    else:
        sections["the_number"] = {"rule": "the_number_key", "token": out["the_number_key"]}
    return {"ok": all(v == "ok" for v in sections.values()), "sections": sections}


def log_safe(result):
    """The result with every model-written token removed. This is the only form that may be logged."""
    return {"ok": result["ok"],
            "sections": {s: v if v == "ok" else {"rule": v["rule"]} for s, v in result["sections"].items()}}


_RULE_WORDS = {
    "number": "the number %s is not in FACTS",
    "spelled_number": "\"%s\" is a spelled-out number; write numbers as digits from FACTS",
    "name": "\"%s\" is not a name in FACTS; start sentences with an ordinary word or a name from FACTS",
    "spotlight_player": "spotlight.player \"%s\" is not a player's full name in FACTS",
    "the_number_key": "the_number_key \"%s\" is not a key in FACTS numbers",
}


def retry_note(result):
    """One plain message naming each failed section, sent back to the model for its one retry.
    Never logged: it contains model-written tokens."""
    parts = []
    for s in SECTIONS:
        v = result["sections"].get(s, "ok")
        if v == "ok":
            continue
        if v["rule"] == "schema":
            return "Your answer did not match the required JSON shape. Return exactly the keys asked for."
        parts.append("%s: %s" % (s, _RULE_WORDS[v["rule"]] % v["token"]))
    return ("Your answer used things that are not in FACTS. " + "; ".join(parts) +
            ". Use only numbers and names that appear in FACTS.") if parts else ""
