"""voice_run result -> what issue.html renders for one voice. Pure: no network, no model.

Each voice gets its own page (server-rendered links, like the edition toggle, Req 10.1b-i), so
the headline, recap, spotlight and The Number always come from one voice's one answer and the
page works with no JavaScript and prints only that voice.

Dropped sections, one at a time:
- headline -> the final score line (template fallback)
- recap    -> "The writers' room passed on this one."
- spotlight-> panel omitted
- the_number -> the deterministic default from the facts sheet
"""
from zine.voices import VOICE_ORDER, VOICES

VOICE_SLUG = {"the_call": "", "film_room": "film-room/"}  # the_call is the default page


def page_path(game_id, edition, voice):
    return "game/%s/%s/%sindex.html" % (game_id, edition, VOICE_SLUG[voice])


def root_prefix(voice):
    """Relative path from a voice page back to the site root."""
    return "../../../" + ("../" if VOICE_SLUG[voice] else "")


def voice_links(f, edition, voice):
    """[{label, url, current}] for the voice switcher on one page, in VOICE_ORDER."""
    pre = root_prefix(voice)
    return [{"label": VOICES[v]["label"], "url": pre + page_path(f["game_id"], edition, v),
             "current": v == voice} for v in VOICE_ORDER]


def edition_urls(f, voice):
    """The other edition in the same voice."""
    pre = root_prefix(voice)
    return {t["abbrev"]: pre + page_path(f["game_id"], t["abbrev"], voice) for t in (f["home"], f["away"])}


def the_number(f, key=None):
    if key not in f.get("number_labels", {}) or key not in f.get("numbers", {}):
        key = f.get("the_number_key")
    if key not in f.get("numbers", {}):
        return None
    return {"value": f["numbers"][key], "caption": f.get("number_labels", {}).get(key, ""), "key": key}


def _spotlight(sp, f):
    line = next((l for l in f.get("player_lines", []) if l["player"] == sp["player"]), None)
    if line is None:  # the lock already requires this; belt and braces
        return None
    team = f["home"] if line["team_abbrev"] == f["home"]["abbrev"] else f["away"]
    words = sp["player"].split()
    stats = [{"value": line[k], "label": lbl} for k, lbl in (("pts", "PTS"), ("reb", "REB"), ("ast", "AST"))
             if k in line and k not in f.get("dropped_categories", [])]
    return {"player": sp["player"], "initials": (words[0][0] + words[-1][0]).upper(),
            "team": team["team"], "stats": stats, "text": sp["text"]}


def build(result, f):
    """None when every section was dropped (the whole voice passed)."""
    s = result["sections"] if result else {}
    if not any(s.values()):
        return None
    return {
        "label": VOICES[result["voice"]]["label"],
        "headline": s.get("headline"),
        "recap": s.get("recap"),
        "spotlight": _spotlight(s["spotlight"], f) if s.get("spotlight") else None,
        "number_key": s.get("the_number"),
    }
