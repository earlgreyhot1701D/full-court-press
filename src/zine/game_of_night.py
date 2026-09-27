"""Game of the Night: a deterministic interest score. Pure: no network, never a model.

Rules live in gotn_rules.json so they can be tuned without touching code. Each rule adds
points; the highest score wins; a tie goes to the later tip (Requirement 4).
"""
import json
import os

_RULES = os.path.join(os.path.dirname(__file__), "gotn_rules.json")


def load_rules(path=_RULES):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def score(facts, rules):
    """Returns (points, reasons). Reasons are for the owner's log, never for the page."""
    pts, why = 0, []
    margin = facts.get("final_margin")
    if margin is not None and margin <= rules["close_margin_max"]:
        pts += rules["close_margin_pts"]
        why.append("close: %d" % margin)
    if facts.get("overtime_periods"):
        pts += rules["overtime_pts"]
        why.append("overtime")
    if any(n["type"] == "30plus" for n in facts.get("notable", [])):
        pts += rules["thirty_pt_game_pts"]
        why.append("30-point game")
    if any(n["type"] == "triple_double" for n in facts.get("notable", [])):
        pts += rules["triple_double_pts"]
        why.append("triple-double")
    if facts.get("winner_max_deficit", 0) >= rules["comeback_min"]:
        pts += rules["comeback_pts"]
        why.append("comeback from %d" % facts["winner_max_deficit"])
    return pts, why


def pick(facts_list, rules=None, eligible=None):
    """Returns the game_id of the Game of the Night, or None for an empty slate.
    eligible: optional set of game_ids that can be featured (the winner's page has a recap).
    If none of the games qualify, every game stays in the running."""
    if not facts_list:
        return None
    rules = rules or load_rules()
    if eligible is not None:
        facts_list = [f for f in facts_list if f["game_id"] in eligible] or facts_list
    ranked = sorted(facts_list, key=lambda f: (score(f, rules)[0], f["tip_time_utc"]), reverse=True)
    return ranked[0]["game_id"]
