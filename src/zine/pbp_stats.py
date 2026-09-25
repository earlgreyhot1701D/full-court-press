"""Per-player statistics counted from WNBA play-by-play. Pure: no network, no model.

Why this exists: WNBA box scores (player_stats) are on a data tier this project does not
buy, so the stat line is counted here from the play-by-play, which is. See Requirement 3b
and design.md "pbp_stats.py".

What the feed gives us (confirmed Sep 24 against the golden set, fixtures/golden/PLAY_TYPES.md):
- A play has no player field. Every name comes from `text`.
- `team` on a play is the shooter's or ball-handler's team.
- Rebounds and turnovers have their own play types. Assists, steals and blocks do not:
  they ride inside other plays' text, e.g.
    "Makayla Timpson makes 1-foot layup (Caitlin Clark assists)"   assister: same team
    "Angel Reese bad pass turnover (Aliyah Boston steals)"         stealer: other team
    "Aliyah Boston blocks Angel Reese's two point shot"            blocker: other team
- Team events exist and are not player events: "Fever defensive team rebound",
  "shot clock turnover".

Attribution is exact string matching only, never fuzzy. A game's roster is the current
roster from the players endpoint plus every name in that game's own substitution lines,
with the team taken from the substitution play. The substitution lines matter: the players
endpoint returns who is on a team now, and a player who has since moved would otherwise
be missing from the game she played in (Jaylyn Sherrod, game 25014).

Gates (Requirement 3b):
- Points: each team's player points must equal its final score from the games endpoint.
  Any unattributed scoring play, or any mismatch, drops every derived stat for the game.
- Every other category is dropped alone, for that game only, if any of its events is
  unattributed or credited to the wrong team, or if it fails its sanity check.
A dropped category is absent from the output, never zero.
"""
import re

CATEGORIES = ("reb", "ast", "stl", "blk", "to")
_SUB = re.compile(r"^(.+?) enters the game for (.+?)\s*$")
_EMBED = re.compile(r"\(([^()]+?) (assists|steals)\)")


def _abbr(team):
    return (team or {}).get("abbreviation")


def build_roster(roster_lists, plays):
    """roster_lists: {abbr: [player dicts from /players]}. Returns ({name: abbr}, conflicts).

    Substitution lines from this game override the current-roster team, because they
    record where the player was on the night. A name claimed by both teams is a conflict
    and is left out, so it can never be credited.
    """
    roster = {}
    for abbr, players in roster_lists.items():
        for p in players:
            name = ("%s %s" % (p.get("first_name", ""), p.get("last_name", ""))).strip()
            if name:
                roster[name] = abbr
    seen = {}
    for p in plays:
        m = _SUB.match(p.get("text") or "")
        team = _abbr(p.get("team"))
        if not m or not team:
            continue
        for name in (m.group(1).strip(), m.group(2).strip()):
            seen.setdefault(name, set()).add(team)
    conflicts = []
    for name, teams in seen.items():
        if len(teams) > 1:
            conflicts.append(name)
            roster.pop(name, None)
        else:
            roster[name] = next(iter(teams))
    return roster, sorted(conflicts)


def _lead(text, names_by_len):
    """The rostered name the text starts with, followed by a space. Exact, longest first."""
    for name in names_by_len:
        if text.startswith(name + " "):
            return name
    return None


def count(plays, home, away, roster_lists):
    """home / away: {"abbrev": str, "score": int} from the games endpoint.

    Returns a dict:
      reconciled      bool, points gate
      player_lines    list of per-player dicts (empty if not reconciled); dropped
                      categories are absent from every line
      categories      {cat: {"ok": bool, "reason": str|None}}
      team_points     {abbr: derived points}
      discrepancy     None, or {abbr: {"expected", "derived"}, "unattributed_points"}
      unattributed    {cat: count}  (owner-facing, never shown to visitors)
      overtime_periods  from the plays: max period minus 4, floor 0
      roster_conflicts  names claimed by both teams in substitution lines
    """
    teams = {home["abbrev"], away["abbrev"]}
    opp = {home["abbrev"]: away["abbrev"], away["abbrev"]: home["abbrev"]}
    roster, conflicts = build_roster(roster_lists, plays)
    names = sorted(roster, key=len, reverse=True)

    lines = {}
    def line(name):
        if name not in lines:
            lines[name] = {"player": name, "team_abbrev": roster[name], "pts": 0, "fgm": 0,
                           "ftm": 0, "oreb": 0, "dreb": 0, "reb": 0, "ast": 0, "stl": 0,
                           "blk": 0, "to": 0}
        return lines[name]

    unattr = {c: 0 for c in ("pts",) + CATEGORIES}
    wrong_team = {c: 0 for c in CATEGORIES}
    team_pts = {t: 0 for t in teams}
    team_fgm = {t: 0 for t in teams}
    team_to = {t: 0 for t in teams}          # player and team turnovers
    team_fg_miss = {t: 0 for t in teams}     # missed field goal attempts
    unattr_pts = 0
    max_period = 0

    for p in plays:
        text = p.get("text") or ""
        ptype = (p.get("type") or "").replace("\n", " ")
        low = text.lower()
        team = _abbr(p.get("team"))
        max_period = max(max_period, p.get("period") or 0)
        lead = _lead(text, names)

        # scoring
        if p.get("scoring_play"):
            v = p.get("score_value") or 0
            if team in teams:
                team_pts[team] += v
            if lead and roster[lead] == team:
                ln = line(lead)
                ln["pts"] += v
                if v == 1:
                    ln["ftm"] += 1
                elif v in (2, 3):
                    ln["fgm"] += 1
                    team_fgm[team] += 1
            else:
                unattr["pts"] += 1
                unattr_pts += v
            for m in _EMBED.finditer(text):
                if m.group(2) != "assists":
                    continue
                n = m.group(1).strip()
                if n not in roster:
                    unattr["ast"] += 1
                elif roster[n] != team:
                    wrong_team["ast"] += 1
                else:
                    line(n)["ast"] += 1
            continue

        # missed field goal (for the blocks sanity check); free throws excluded
        if " misses " in text and not ptype.startswith("Free Throw") and team in teams:
            team_fg_miss[team] += 1

        # blocks: "<blocker> blocks <shooter>'s ..."; blocker is on the other team
        if lead and text.startswith(lead + " blocks "):
            if team in teams:
                team_fg_miss[team] += 1        # a blocked shot is a missed shot; the text never says "misses"
            if team in teams and roster[lead] == opp[team]:
                line(lead)["blk"] += 1
            else:
                wrong_team["blk"] += 1
            continue
        if " blocks " in text and not lead:
            unattr["blk"] += 1
            continue

        # rebounds
        if ptype in ("Defensive Rebound", "Offensive Rebound"):
            if "team rebound" in low:
                continue                                   # a team event, not a player's
            if lead and roster[lead] == team:
                ln = line(lead)
                ln["dreb" if ptype.startswith("Defensive") else "oreb"] += 1
                ln["reb"] += 1
            elif lead:
                wrong_team["reb"] += 1
            else:
                unattr["reb"] += 1
            continue

        # turnovers, and steals embedded in them
        if "turnover" in ptype.lower() or " turnover" in low or ptype == "Traveling":
            if team in teams:
                team_to[team] += 1
            if lead:
                if roster[lead] == team:
                    line(lead)["to"] += 1
                else:
                    wrong_team["to"] += 1
            elif not text[:1].isupper() or low.startswith("shot clock"):
                pass                                       # team turnover
            else:
                unattr["to"] += 1
            for m in _EMBED.finditer(text):
                if m.group(2) != "steals":
                    continue
                n = m.group(1).strip()
                if n not in roster:
                    unattr["stl"] += 1
                elif team in teams and roster[n] == opp[team]:
                    line(n)["stl"] += 1
                else:
                    wrong_team["stl"] += 1

    # points gate
    derived = {t: sum(l["pts"] for l in lines.values() if l["team_abbrev"] == t) for t in teams}
    expected = {home["abbrev"]: home["score"], away["abbrev"]: away["score"]}
    reconciled = unattr["pts"] == 0 and all(derived[t] == expected[t] for t in teams)
    discrepancy = None
    if not reconciled:
        discrepancy = {t: {"expected": expected[t], "derived": derived[t]} for t in teams}
        discrepancy["unattributed_points"] = unattr_pts

    # per-category gates
    cats = {}
    for c in CATEGORIES:
        reason = None
        if unattr[c]:
            reason = "%d unattributed" % unattr[c]
        elif wrong_team[c]:
            reason = "%d credited to the wrong team" % wrong_team[c]
        else:
            for t in teams:
                tot = sum(l[c] for l in lines.values() if l["team_abbrev"] == t)
                if c == "ast" and tot > team_fgm[t]:
                    reason = "%s assists exceed made field goals" % t
                elif c == "blk" and tot > team_fg_miss[opp[t]]:
                    reason = "%s blocks exceed opponent misses" % t
                elif c == "stl" and tot > team_to[opp[t]]:
                    reason = "%s steals exceed opponent turnovers" % t
                if reason:
                    break
        cats[c] = {"ok": reason is None, "reason": reason}

    out_lines = []
    if reconciled:
        dropped = [c for c in CATEGORIES if not cats[c]["ok"]]
        for l in sorted(lines.values(), key=lambda x: (-x["pts"], x["player"])):
            row = dict(l, source="play_by_play")
            for c in dropped:
                row.pop(c, None)
                if c == "reb":
                    row.pop("oreb", None)
                    row.pop("dreb", None)
            out_lines.append(row)

    return {
        "reconciled": reconciled,
        "player_lines": out_lines,
        "categories": cats,
        "team_points": derived,
        "discrepancy": discrepancy,
        "unattributed": {c: unattr[c] for c in unattr},
        "overtime_periods": max(0, max_period - 4),
        "roster_conflicts": conflicts,
    }
