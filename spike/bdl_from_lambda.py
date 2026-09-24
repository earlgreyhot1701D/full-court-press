"""Block 0 spike 0.4: does BALLDONTLIE answer from a Lambda IP, and which
endpoints return 200 on our current tier?

Throwaway. One flat handler. Reads the API key from SSM at runtime, calls four
WNBA endpoints in order with >=1s spacing and a 10s timeout, reports status code
and byte size per call. Never prints the key.
"""
import json
import time
import urllib.request
import urllib.error

import boto3

BASE = "https://api.balldontlie.io"
KEY_PARAM = "/full-court-press/bdl-api-key"
TIMEOUT = 10
SPACING = 1.0  # seconds, minimum between requests


def _get_key():
    ssm = boto3.client("ssm")
    resp = ssm.get_parameter(Name=KEY_PARAM, WithDecryption=True)
    return resp["Parameter"]["Value"]


def _call(path, api_key):
    """Return (status_code, byte_size, parsed_or_none). Never logs the key or URL header."""
    url = BASE + path
    req = urllib.request.Request(url, headers={"Authorization": api_key})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            body = r.read()
            status = r.getcode()
    except urllib.error.HTTPError as e:
        body = e.read() or b""
        status = e.code
    except Exception as e:
        return (None, 0, {"error": repr(e)})
    parsed = None
    try:
        parsed = json.loads(body.decode("utf-8"))
    except Exception:
        parsed = None
    return (status, len(body), parsed)


def _pick_date_and_game(api_key, start_date, scan_days):
    """Scan backward from start_date for a date whose games call returns data.
    Returns (date_used, game_id, first_games_status, first_games_bytes, scan_trace)."""
    from datetime import date, timedelta
    y, m, d = (int(x) for x in start_date.split("-"))
    base = date(y, m, d)
    trace = []
    for i in range(scan_days):
        day = (base - timedelta(days=i)).isoformat()
        s, n, parsed = _call(f"/wnba/v1/games?dates[]={day}", api_key)
        ngames = len(parsed.get("data", [])) if isinstance(parsed, dict) else 0
        trace.append({"date": day, "status": s, "n_games": ngames})
        if s != 200:
            # auth/tier problem: stop scanning, report this immediately
            return day, None, s, n, trace
        if ngames:
            gid = None
            for g in parsed["data"]:
                if g.get("id") is not None:
                    gid = g.get("id")
                    if str(g.get("status", "")).lower() in ("final", "finished", "closed"):
                        break
            return day, gid, s, n, trace
        time.sleep(SPACING)
    return trace[-1]["date"] if trace else start_date, None, trace[-1]["status"] if trace else None, 0, trace


def handler(event, context):
    api_key = _get_key()

    start_date = (event or {}).get("date", "2026-09-22")
    scan_days = int((event or {}).get("scan_days", 10))

    results = []

    # 1) games: scan recent dates for one with data
    game_date, game_id, g_status, g_bytes, scan_trace = _pick_date_and_game(api_key, start_date, scan_days)
    results.append({"endpoint": "games", "status": g_status, "bytes": g_bytes, "date_used": game_date})
    time.sleep(SPACING)

    # 2) player_stats for that game
    if game_id is not None:
        s, n, _ = _call(f"/wnba/v1/player_stats?game_ids[]={game_id}", api_key)
        results.append({"endpoint": "player_stats", "status": s, "bytes": n, "game_id": game_id})
    else:
        results.append({"endpoint": "player_stats", "status": "SKIPPED_no_game_id", "bytes": 0})
    time.sleep(SPACING)

    # 3) standings
    s, n, _ = _call("/wnba/v1/standings", api_key)
    results.append({"endpoint": "standings", "status": s, "bytes": n})
    time.sleep(SPACING)

    # 4) plays for that game
    if game_id is not None:
        s, n, _ = _call(f"/wnba/v1/plays?game_id={game_id}", api_key)
        results.append({"endpoint": "plays", "status": s, "bytes": n, "game_id": game_id})
    else:
        results.append({"endpoint": "plays", "status": "SKIPPED_no_game_id", "bytes": 0})

    return {"date": game_date, "game_id": game_id, "results": results, "scan_trace": scan_trace}
