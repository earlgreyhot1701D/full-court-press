"""Standings data for the issue and Around the League. Pure: no network, no model.

Two things about the standings endpoint, both found Sep 24 on the golden fetch:
- It returns every season since 2008 unless one is requested (235 rows), so rows are always
  filtered to the game's season.
- Its `playoff_seed` field is the team's rank within its conference, and every team has one:
  Seattle at 8-36 is "seed 8". Printing it as a seed would tell a fan her team made the playoffs.
  So it is published as a place in the conference ("6th in the East"), never as a seed.

Only record and conference place are published, per task 2.6c.
"""

_CONF = {"Eastern Conference": "East", "Western Conference": "West"}


def ordinal(n):
    if 10 <= n % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return "%d%s" % (n, suffix)


def standings_line(rows, season, abbrevs):
    """Returns {abbr: {"wins", "losses", "conference", "conference_rank", "place"}}.

    A team with no row for that season, more than one, or a missing field, is left out rather
    than guessed.
    """
    found = {}
    for r in rows:
        if r.get("season") != season:
            continue
        ab = (r.get("team") or {}).get("abbreviation")
        if ab in abbrevs:
            found.setdefault(ab, []).append(r)
    out = {}
    for ab, rs in found.items():
        if len(rs) != 1:
            continue
        r = rs[0]
        conf = _CONF.get(r.get("conference"))
        rank = r.get("playoff_seed")
        if r.get("wins") is None or r.get("losses") is None or not conf or not rank:
            continue
        out[ab] = {"wins": r["wins"], "losses": r["losses"], "conference": conf,
                   "conference_rank": rank, "place": "%s in the %s" % (ordinal(rank), conf)}
    return out
