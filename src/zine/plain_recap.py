"""The floor under every page: a short recap written by code from the counted facts.

Shown only when the AI recap for a page was cut (the fact lock, banned words, or the render-time
re-check). Deterministic, no model call, and every number comes straight from the facts sheet, so
it is true by construction. Told from the edition's side, honest about a loss.
"""


def _nick(team):
    """'Golden State Valkyries' -> 'the Valkyries'. Every WNBA nickname is one word."""
    return "the " + team["team"].split()[-1]


def _cap(s):
    return s[0].upper() + s[1:]


def _period(q):
    if q <= 4:
        return "the %s quarter" % ("1st", "2nd", "3rd", "4th")[q - 1]
    return "overtime" if q == 5 else "the %s overtime" % ("2nd", "3rd", "4th", "5th")[min(q - 6, 3)]


def _article(detail):
    return "an" if detail.split("-")[0] in ("8", "11", "18") else "a"


def build(f, edition):
    """Returns a paragraph (str), or None if the facts are too thin to say anything."""
    teams = {f["home"]["abbrev"]: f["home"], f["away"]["abbrev"]: f["away"]}
    if edition not in teams or f.get("winner_abbrev") not in teams:
        return None
    me = teams[edition]
    them = next(t for ab, t in teams.items() if ab != edition)
    win = teams[f["winner_abbrev"]]
    lose = them if win is me else me
    ot = " in overtime" if f.get("overtime_periods") else ""
    out = []

    if win is me:
        out.append("%s beat %s %d-%d%s." % (_cap(_nick(me)), _nick(them), win["score"], lose["score"], ot))
    else:
        out.append("%s lost to %s %d-%d%s." % (_cap(_nick(me)), _nick(them), win["score"], lose["score"], ot))

    if (f.get("winner_max_deficit") or 0) >= 8:  # "trailed by 2" in a blowout is noise
        out.append("%s trailed by as many as %d and still won." % (_cap(_nick(win)), f["winner_max_deficit"]))

    qh, qa = f.get("quarters", {}).get("home", []), f.get("quarters", {}).get("away", [])
    if qh and len(qh) == len(qa):
        h, a = qh[-1], qa[-1]
        if h != a:
            t = f["home"] if h > a else f["away"]
            out.append("%s won %s %d-%d." % (_cap(_nick(t)), _period(len(qh)), max(h, a), min(h, a)))

    runs = f.get("runs") or []
    if runs:
        r = max(runs, key=lambda r: r["points"])
        t = teams.get(r["team_abbrev"])
        if t:
            out.append("%s went on %s %s run in %s." % (_cap(_nick(t)), _article(r["detail"]), r["detail"], _period(r["quarter"])))

    lead = next((ld for ld in f.get("leaders", []) if ld["team_abbrev"] == edition and ld["category"] == "points"), None)
    if lead:
        out.append("%s led %s with %d points." % (lead["player"], _nick(me), lead["value"]))

    st = (f.get("standings_line") or {}).get(edition)
    if st:
        out.append("%s are %s at %d-%d." % (_cap(_nick(me)), st["place"], st["wins"], st["losses"]))

    return " ".join(out) if out else None
