"""Block 0 follow-up spike: are our WNBA endpoint PATHS correct?

The NBA-shaped paths were inferred, not verified for WNBA. GOAT endpoints
(standings, plays) returned 200 while the ALL-STAR endpoint (player_stats)
returned 401, which is not a tier ladder. This probe tries several candidate
paths against game_id 25072 and captures the full body of one 401 so we can
tell an unknown-route error from a tier-denied error.

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


def _call(path, api_key, want_body=False):
    req = urllib.request.Request(BASE + path, headers={"Authorization": api_key})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            body = r.read()
            status = r.getcode()
    except urllib.error.HTTPError as e:
        body = e.read() or b""
        status = e.code
    except Exception as e:
        return {"path": path, "status": None, "bytes": 0, "error": repr(e)}
    out = {"path": path, "status": status, "bytes": len(body)}
    if want_body:
        # cap the captured body so we never dump anything huge; 401 bodies are tiny
        out["body"] = body[:500].decode("utf-8", "replace")
    return out


def handler(event, context):
    api_key = _get_key()
    gid = (event or {}).get("game_id", 25072)

    results = []

    # First, read the game to extract team ids for the players endpoint.
    team_id = None
    g = _call(f"/wnba/v1/games?dates[]=2026-09-22", api_key)
    results.append(g)
    time.sleep(SPACING)

    # candidate paths
    candidates = [
        f"/wnba/v1/player_stats?game_ids[]={gid}",
        f"/wnba/v1/stats?game_ids[]={gid}",
        f"/wnba/v1/box_scores?game_ids[]={gid}",
        f"/wnba/v1/box_scores/live",
    ]

    first_401_body = None
    for p in candidates:
        # capture the body on the first 401 we see
        want = first_401_body is None
        r = _call(p, api_key, want_body=want)
        if r.get("status") == 401 and first_401_body is None:
            first_401_body = {"path": p, "body": r.get("body")}
        # do not keep large bodies in the per-path summary
        r.pop("body", None)
        results.append(r)
        time.sleep(SPACING)

    # players endpoint needs a team id; fetch it now from the game
    try:
        gk = _call(f"/wnba/v1/games?dates[]=2026-09-22", api_key)
        # re-fetch parsed to get team ids
        req = urllib.request.Request(BASE + f"/wnba/v1/games?dates[]=2026-09-22",
                                     headers={"Authorization": api_key})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            parsed = json.loads(r.read().decode("utf-8"))
        for game in parsed.get("data", []):
            if game.get("id") == gid:
                team_id = (game.get("home_team") or {}).get("id") or (game.get("visitor_team") or {}).get("id")
                break
        if team_id is None and parsed.get("data"):
            team_id = (parsed["data"][0].get("home_team") or {}).get("id")
    except Exception as e:
        results.append({"path": "team_id_lookup", "status": None, "bytes": 0, "error": repr(e)})
    time.sleep(SPACING)

    if team_id is not None:
        want = first_401_body is None
        r = _call(f"/wnba/v1/players?team_ids[]={team_id}", api_key, want_body=want)
        if r.get("status") == 401 and first_401_body is None:
            first_401_body = {"path": f"/wnba/v1/players?team_ids[]={team_id}", "body": r.get("body")}
        r.pop("body", None)
        r["team_id_used"] = team_id
        results.append(r)
    else:
        results.append({"path": "players", "status": "SKIPPED_no_team_id", "bytes": 0})

    return {"game_id": gid, "results": results, "first_401_body": first_401_body}
