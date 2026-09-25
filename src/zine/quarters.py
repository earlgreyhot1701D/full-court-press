"""Points per period, from the play-by-play. Pure: no network, no model.

The games endpoint carries only the final score, not quarter scores (confirmed Sep 24 on the
golden set), so each period's points come from the running score on the plays: the score at
the end of a period minus the score at the end of the one before.

Cross-check: the periods must add up to the final score from the games endpoint. If they do
not, the function returns None and the issue publishes without a quarter-by-quarter panel.
That check alone is not enough: a late-logged record once made Q1 read 20-20 instead of 26-20
while the totals still matched. So plays are walked in true game order (zine.timeline), and a
running score that goes down within that order returns None.
"""

from zine.timeline import in_game_order


def period_scores(plays, home_final, away_final):
    """Returns {"home": [p1, p2, ...], "away": [...], "periods": n} or None if it cannot be trusted."""
    last = {}
    top = (0, 0)
    for p in in_game_order(plays):
        per = p.get("period")
        hs, as_ = p.get("home_score"), p.get("away_score")
        if per is None or hs is None or as_ is None:
            continue
        if hs < top[0] or as_ < top[1]:
            return None                   # the score went down in true game order: do not trust it
        top = (hs, as_)
        last[per] = (hs, as_)
    if not last:
        return None
    periods = sorted(last)
    if periods != list(range(1, periods[-1] + 1)):
        return None                       # a missing period means a gap in the feed
    home, away, prev = [], [], (0, 0)
    for per in periods:
        hs, as_ = last[per]
        if hs < prev[0] or as_ < prev[1]:
            return None                   # a running score must never go down
        home.append(hs - prev[0])
        away.append(as_ - prev[1])
        prev = (hs, as_)
    if sum(home) != home_final or sum(away) != away_final:
        return None
    return {"home": home, "away": away, "periods": len(periods)}
