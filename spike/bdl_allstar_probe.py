"""Block 0 follow-up: confirm exactly what WNBA ALL-STAR grants on this key.

WNBA tiers differ from NBA. Per https://wnba.balldontlie.io "Account Tiers":
ALL-STAR = standings, play-by-play, active players, player injuries.
GOAT = player_stats, team_stats, season stats.

Throwaway. Reads the key from SSM at runtime, never prints it.
"""
import json
import time
import urllib.request
import urllib.error

import boto3

BASE = "https://api.balldontlie.io"
KEY_PARAM = "/full-court-press/bdl-api-key"
TIMEOUT = 10
SPACING = 1.0


def _get_key():
    ssm = boto3.client("ssm")
    return ssm.get_parameter(Name=KEY_PARAM, WithDecryption=True)["Parameter"]["Value"]


def _call(path, api_key):
    req = urllib.request.Request(BASE + path, headers={"Authorization": api_key})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            body = r.read()
            status = r.getcode()
    except urllib.error.HTTPError as e:
        body = e.read() or b""
        status = e.code
    except Exception as e:
        return {"path": path, "status": None, "bytes": 0, "error": repr(e)}, None
    parsed = None
    try:
        parsed = json.loads(body.decode("utf-8"))
    except Exception:
        parsed = None
    return {"path": path, "status": status, "bytes": len(body)}, parsed


def handler(event, context):
    api_key = _get_key()
    gid = (event or {}).get("game_id", 25072)

    results = []
    plays_count = None

    paths = [
        "/wnba/v1/standings",
        f"/wnba/v1/plays?game_id={gid}",
        "/wnba/v1/players/active",
        "/wnba/v1/player_injuries",
    ]

    for p in paths:
        summary, parsed = _call(p, api_key)
        # count plays for the game
        if p.startswith("/wnba/v1/plays") and isinstance(parsed, dict):
            data = parsed.get("data")
            if isinstance(data, list):
                plays_count = len(data)
                meta = parsed.get("meta") or {}
                summary["next_cursor"] = meta.get("next_cursor")
                summary["per_page"] = meta.get("per_page")
        results.append(summary)
        time.sleep(SPACING)

    return {"game_id": gid, "results": results, "plays_count_first_page": plays_count}
