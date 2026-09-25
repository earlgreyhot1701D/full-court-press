"""Fetch the golden set from BALLDONTLIE into fixtures/golden/, raw and unmodified.

Run by the owner, on her own machine, through tools/fetch_golden.ps1, which pulls the
API key from SSM into an environment variable for the life of this one process.
This script never prints, logs or writes the key. It writes only the raw JSON the API
returned, plus a short report of status codes and byte sizes.

Requests: 5 games x (game + plays + 2 rosters, paginated) + standings once. About 25
calls, one second apart, well inside the 60-per-run cap in tech.md. Standard library only.
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

# Chosen Sep 24, see LEDGER. OT, one-point, three-point, blowout, ordinary; covers all three
# expansion teams (POR, TOR, GS), whose colours are still unverified.
GOLDEN = [25014, 25071, 25057, 25066, 25064]
BASE = "https://api.balldontlie.io"
ROOT = Path(__file__).resolve().parent.parent / "fixtures" / "golden"
REPORT = ROOT / "FETCH-REPORT.txt"
MAX_ROSTER_PAGES = 5

KEY = os.environ.get("BDL_API_KEY", "").strip()
lines = []


def note(msg):
    lines.append(msg)


def call(path):
    time.sleep(1)  # at least one second between requests, per tech.md
    req = urllib.request.Request(BASE + path, headers={"Authorization": KEY})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            body = r.read()
            return r.getcode(), body
    except urllib.error.HTTPError as e:
        return e.code, b""
    except Exception as e:  # network error: record the type, never the request
        return None, type(e).__name__.encode()


def save(path, body):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(body)


def roster(team_id, dest):
    pages, cursor = [], None
    for _ in range(MAX_ROSTER_PAGES):
        q = "/wnba/v1/players?team_ids[]=%d&per_page=100" % team_id
        if cursor:
            q += "&cursor=%s" % cursor
        code, body = call(q)
        note("  roster team %d page %d: %s, %d bytes" % (team_id, len(pages) + 1, code, len(body)))
        if code != 200:
            return False
        data = json.loads(body)
        pages.append(data)
        cursor = (data.get("meta") or {}).get("next_cursor")
        if not cursor:
            break
    merged = {"data": [p for page in pages for p in page.get("data", [])],
              "meta": {"pages": len(pages), "source": "players?team_ids[]=%d" % team_id}}
    save(dest, json.dumps(merged, indent=1).encode())
    return True


def main():
    if not KEY:
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text("ABORTED: BDL_API_KEY was empty. Nothing fetched.\n")
        return 1
    ok = True
    for gid in GOLDEN:
        d = ROOT / str(gid)
        code, body = call("/wnba/v1/games/%d" % gid)
        note("game %d: %s, %d bytes" % (gid, code, len(body)))
        if code != 200:
            ok = False
            continue
        save(d / "game.json", body)
        g = json.loads(body)["data"]
        code, body = call("/wnba/v1/plays?game_id=%d" % gid)
        note("  plays: %s, %d bytes" % (code, len(body)))
        if code == 200:
            save(d / "plays.json", body)
        else:
            ok = False
        for side in ("home_team", "visitor_team"):
            tid = g[side]["id"]
            if not roster(tid, d / ("roster_%s.json" % g[side]["abbreviation"])):
                ok = False
    code, body = call("/wnba/v1/standings")
    note("standings: %s, %d bytes" % (code, len(body)))
    if code == 200:
        save(ROOT / "standings.json", body)
    else:
        ok = False
    note("RESULT: %s" % ("OK" if ok else "INCOMPLETE, see above"))
    REPORT.write_text("\n".join(lines) + "\n")
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
