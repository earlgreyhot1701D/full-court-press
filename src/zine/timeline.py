"""Put plays back in the order they happened. Pure: no network, no model.

The feed logs some events late (found Sep 24 on the golden set: 19 records across 4 of 5 games).
A late record sits later in the list than it happened, sometimes filed under an earlier period,
and carries the scoreboard from the moment it happened, so read in list order the score appears
to drop and then jump back. Anything that walks the game in sequence (runs, quarter scores)
must use true game order: period ascending, then game clock descending, since the clock counts
down. Ties keep the feed's own order.

Counting stats does not need this: a total does not depend on order.
"""


def clock_seconds(clock):
    """'7:52' -> 472.0, '18.3' -> 18.3. Unparseable -> None."""
    if clock is None:
        return None
    s = str(clock).strip()
    try:
        if ":" in s:
            m, sec = s.split(":", 1)
            return int(m) * 60 + float(sec)
        return float(s)
    except ValueError:
        return None


def in_game_order(plays):
    """Plays sorted by (period, clock descending, original position). Plays with no period or an
    unparseable clock keep their position relative to the play before them."""
    keyed = []
    last_key = (0, float("inf"))
    for i, p in enumerate(plays):
        per = p.get("period")
        secs = clock_seconds(p.get("clock"))
        if per is None or secs is None:
            key = last_key
        else:
            key = (per, -secs)
            last_key = key
        keyed.append((key, i, p))
    keyed.sort(key=lambda k: (k[0], k[1]))
    return [p for _, _, p in keyed]
