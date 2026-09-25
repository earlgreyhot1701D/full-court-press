"""TEMP: check max play-by-play period for the closest games, to find any OT."""
import json
import os
import time
import urllib.request

k = os.environ["BDL_API_KEY"]
res = {}


def maxperiod(gid):
    req = urllib.request.Request(
        "https://api.balldontlie.io/wnba/v1/plays?game_id=%d" % gid,
        headers={"Authorization": k},
    )
    d = json.load(urllib.request.urlopen(req, timeout=10))
    plays = d.get("data", [])
    mp = max((p.get("period") or 0) for p in plays) if plays else 0
    return [mp, len(plays)]


# the closest-margin games are the OT candidates
for gid in [25057, 25033, 25062, 25047, 25037, 25043, 25036]:
    try:
        res[str(gid)] = maxperiod(gid)
    except Exception as e:
        res[str(gid)] = ["err", repr(e)]
    time.sleep(1)

with open("_ot_probe.json", "w", encoding="utf-8") as fh:
    json.dump(res, fh)
