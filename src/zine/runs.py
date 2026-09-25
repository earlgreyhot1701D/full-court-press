"""Scoring runs: stretches of unanswered points. Pure: no network, no model.

A run is points scored by one team while the other scores none. Emitted when it reaches
MIN_RUN points. A run never crosses a period boundary: it closes at the end of the period,
and the next period starts fresh. That rule exists because a naive walk of the real DAL/PHX
game on Sep 20 merged a second-quarter run into the third.

Scores come from the running home_score/away_score on each play, so a run is measured on
the scoreboard, not on anyone's attribution. Plays are walked in true game order
(zine.timeline), because the feed logs some events late with the scoreboard of their moment.
"""

from zine.timeline import in_game_order

MIN_RUN = 8


def find_runs(plays, home_abbr, away_abbr, min_run=MIN_RUN):
    """Returns runs in game order: [{"quarter", "team_abbrev", "points", "detail", "start_clock", "end_clock"}]."""
    runs = []
    cur = None                           # {"team", "points", "quarter", "start", "end"}
    prev = None                          # (period, home, away)

    def close():
        if cur and cur["points"] >= min_run:
            runs.append({"quarter": cur["quarter"], "team_abbrev": cur["team"],
                         "points": cur["points"], "detail": "%d-0" % cur["points"],
                         "start_clock": cur["start"], "end_clock": cur["end"]})

    for p in in_game_order(plays):
        per, hs, as_ = p.get("period"), p.get("home_score"), p.get("away_score")
        if per is None or hs is None or as_ is None:
            continue
        if prev is None or per != prev[0]:
            close()
            cur = None
            base = prev[1:] if prev else (0, 0)
            prev = (per, base[0], base[1])
        dh, da = hs - prev[1], as_ - prev[2]
        if dh or da:
            scorer = home_abbr if dh > 0 and da == 0 else away_abbr if da > 0 and dh == 0 else None
            pts = dh if scorer == home_abbr else da
            if scorer is None:            # both moved on one play: treat as a break in any run
                close()
                cur = None
            elif cur and cur["team"] == scorer:
                cur["points"] += pts
                cur["end"] = p.get("clock")
            else:
                close()
                cur = {"team": scorer, "points": pts, "quarter": per,
                       "start": p.get("clock"), "end": p.get("clock")}
        prev = (per, hs, as_)
    close()
    return runs
