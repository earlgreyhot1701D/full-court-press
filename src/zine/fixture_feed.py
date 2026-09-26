"""A fake BALLDONTLIE client that serves the golden fixtures, for offline hunter runs (tests and
the local --dry-run, Req 1.6). Never used by the deployed handler.
It answers the games-by-date query using the UTC date of each game, so the hunter's
ask-for-two-dates-and-filter logic is exercised for the West Coast game (25057)."""
import glob
import json
import os
import re

from zine.paths import ROOT

GOLDEN = os.path.join(ROOT, "fixtures", "golden")


class FakeBDL:
    def __init__(self, final=True, fail_plays_for=()):
        self.games, self.plays, self.rosters = {}, {}, {}
        for d in glob.glob(os.path.join(GOLDEN, "[0-9]*")):
            g = json.load(open(os.path.join(d, "game.json")))["data"]
            if not final:
                g = dict(g, status_state="in")
            self.games[g["id"]] = g
            self.plays[g["id"]] = json.load(open(os.path.join(d, "plays.json")))["data"]
            for side in ("home_team", "visitor_team"):
                t = g[side]
                self.rosters[t["id"]] = json.load(open(os.path.join(d, "roster_%s.json" % t["abbreviation"])))["data"]
        self.standings = json.load(open(os.path.join(GOLDEN, "standings.json")))["data"]
        self.fail_plays_for = set(fail_plays_for)
        self.calls = []

    def get_all(self, path, max_pages=5):
        self.calls.append(path.split("?")[0])
        m = re.search(r"dates\[\]=(\d{4}-\d{2}-\d{2})", path)
        if "/games" in path and m:
            return 200, [g for g in self.games.values() if g["date"][:10] == m.group(1)]
        m = re.search(r"plays\?game_id=(\d+)", path)
        if m:
            gid = int(m.group(1))
            return (500, []) if gid in self.fail_plays_for else (200, self.plays[gid])
        m = re.search(r"team_ids\[\]=(\d+)", path)
        if m:
            return 200, self.rosters[int(m.group(1))]
        if path.endswith("/standings"):
            return 200, self.standings
        return 404, []
