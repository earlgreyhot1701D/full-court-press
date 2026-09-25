"""League configuration. Task 2.1.

WNBA is enabled. NBA is a STUB: the season starts late October 2026, after this project's
deadline. BALLDONTLIE serves both leagues from the same shapes with a different path segment,
so turning it on is this flag plus a tier check, since tiers are per sport and are NOT shared
(learned Sep 23: the WNBA table differs from the NBA one).
"""

LEAGUES = {
    "wnba": {"enabled": True, "path": "wnba", "tz": "America/New_York"},
    # STUB(full-court-press): NBA. Set enabled True late Oct 2026 only after confirming the NBA tier
    # includes plays and standings for this key, and adding NBA team colours to team_colors.json.
    "nba": {"enabled": False, "path": "nba", "tz": "America/New_York"},
}

# Filling gaps in the provider's team records, never overriding them.
# Found Sep 24 in the golden fetch: the two 2026 expansion teams come back with an empty city and a
# full_name of just the nickname ("Fire", "Tempo"). Every page would print them that way, and an
# empty city reached allowed_names. Values here apply ONLY where the provider's field is empty.
# Sources: https://en.wikipedia.org/wiki/Portland_Fire, https://en.wikipedia.org/wiki/Toronto_Tempo
TEAM_FILL = {
    "wnba": {
        "POR": {"city": "Portland", "full_name": "Portland Fire"},
        "TOR": {"city": "Toronto", "full_name": "Toronto Tempo"},
    },
}


def complete_team(team, league="wnba"):
    """Returns a copy of a provider team dict with blank city / full_name filled from TEAM_FILL.

    A field the provider supplied is never changed. If a blank field has no fill, full_name falls
    back to "city name" when both exist, else to the nickname, and nothing is ever left empty.
    """
    t = dict(team)
    fill = TEAM_FILL.get(league, {}).get(t.get("abbreviation"), {})
    for field in ("city", "full_name"):
        if not (t.get(field) or "").strip() and fill.get(field):
            t[field] = fill[field]
    if not (t.get("full_name") or "").strip() or t.get("full_name") == t.get("name"):
        if (t.get("city") or "").strip() and t.get("name"):
            t["full_name"] = "%s %s" % (t["city"], t["name"])
        else:
            t["full_name"] = t.get("name") or t.get("abbreviation")
    return t
