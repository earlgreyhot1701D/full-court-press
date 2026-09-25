"""TEMPORARY discovery script (deleted before commit). Reads the BDL key from the
BDL_API_KEY env var (never from disk, never printed), scans recent finished WNBA
games, and classifies each by final margin and overtime so a golden mix can be
picked. Prints only game ids, teams, scores, margin, OT, period counts. No key.
"""
import json
import os
import time
import urllib.request
import urllib.error
from datetime import date, timedelta

KEY = os.environ["BDL_API_KEY"]
BASE = "https://api.balldontlie.io"


def call(path):
    req = urllib.request.Request(BASE + path, headers={"Authorization": KEY})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.getcode(), json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, None
    except Exception as e:
        return None, {"error": repr(e)}


def main():
    # Scan back from a recent in-season date. WNBA 2026 regular season; playoffs
    # start Sep 27. Use dates before "today" in the project timeline (Sep 23-24).
    found = []
    base_day = date(2026, 9, 22)
    for delta in range(0, 58):  # per-run request cap is 60; leave headroom
        d = (base_day - timedelta(days=delta)).isoformat()
        code, data = call("/wnba/v1/games?dates[]=%s" % d)
        if code != 200 or not isinstance(data, dict):
            time.sleep(1)
            continue
        for g in data.get("data", []):
            status = str(g.get("status", ""))
            state = str(g.get("status_state", ""))
            hs, as_ = g.get("home_score"), g.get("away_score")
            if hs is None or as_ is None:
                continue
            # finished only
            if state and state != "final" and "final" not in status.lower():
                continue
            if (hs or 0) == 0 and (as_ or 0) == 0:
                continue
            margin = abs((hs or 0) - (as_ or 0))
            period = g.get("period")
            found.append({
                "id": g.get("id"), "date": d,
                "home": g.get("home_team", {}).get("abbreviation"),
                "away": g.get("visitor_team", {}).get("abbreviation"),
                "hs": hs, "as": as_, "margin": margin,
                "period": period, "status": status, "state": state,
            })
        time.sleep(1)
        # keep scanning until we have found at least one OT game or exhausted the window
        ot_so_far = [x for x in found if (x["period"] or 4) > 4]
        if len(found) >= 60 and ot_so_far:
            break

    # classify
    ot = [g for g in found if (g["period"] or 4) > 4]
    blowout = [g for g in found if g["margin"] >= 20]
    close = [g for g in found if g["margin"] <= 3]
    ordinary = [g for g in found if 8 <= g["margin"] <= 15]

    out = {
        "total": len(found),
        "ot": ot[:8],
        "blowout": blowout[:8],
        "close": close[:8],
        "ordinary": ordinary[:10],
        "all": found,
    }
    with open("_golden_candidates.json", "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)
    print("wrote _golden_candidates.json total=%d ot=%d blowout=%d close=%d ordinary=%d"
          % (len(found), len(ot), len(blowout), len(close), len(ordinary)))


if __name__ == "__main__":
    main()
