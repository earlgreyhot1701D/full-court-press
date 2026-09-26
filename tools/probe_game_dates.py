"""Read-only probe for the Sep 26 deploy finding: how does the games LIST endpoint report `date`,
and which query date does a West Coast game (25071, tip 02:00 UTC Sep 22) come back under?

Prints game id, the raw `date` field, status and status_state only. Never prints the key or a body.
Owner or Kiro runs it with BDL_API_KEY set for this one process (as in tools/fetch_golden.ps1):
    python tools/probe_game_dates.py
"""
import json
import os
import time
import urllib.request

KEY = os.environ["BDL_API_KEY"]
out = {}
for d in ["2026-09-21", "2026-09-22", "2026-09-25", "2026-09-26"]:
    req = urllib.request.Request("https://api.balldontlie.io/wnba/v1/games?dates[]=%s&per_page=100" % d,
                                 headers={"Authorization": KEY})
    try:
        rows = json.load(urllib.request.urlopen(req, timeout=10)).get("data", [])
        out[d] = [{"id": g.get("id"), "date": g.get("date"), "status": g.get("status"),
                   "status_state": g.get("status_state")} for g in rows]
    except Exception as e:
        out[d] = {"error": type(e).__name__}
    time.sleep(1)
print(json.dumps(out, indent=1))
