"""BALLDONTLIE HTTP client. Task 2.2. HTTP only: no parsing beyond JSON, no business logic.

Rules from tech.md and guardrails.md, enforced here rather than trusted to callers:
- Authorization header is the bare key, no "Bearer". The key is never logged.
- At least one second between requests; a hard cap per run (MAX_REQUESTS_PER_RUN, default 60).
- 10 second timeout. 429 backs off (Retry-After if given, else doubling from 2s), 3 tries at most.
- 401 is not retried: it means the tier does not include that endpoint, and retrying wastes the cap.
- Endpoints on the NEVER list are refused before any request is made: odds, player props, player
  injuries, and player_stats (GOAT-only for WNBA; stats are counted from plays instead).
- Every call returns (status, data). Network failures come back as (None, None), never raised.
"""
import json
import os
import time
import urllib.error
import urllib.request

BASE = "https://api.balldontlie.io"
REFUSED = ("/odds", "/player_props", "/player_injuries", "/player_stats")


class CapReached(Exception):
    pass


class Client:
    def __init__(self, key, max_requests=None, spacing=1.0, timeout=10, opener=None, sleep=None, clock=None):
        self._key = key
        self.max_requests = int(max_requests or os.environ.get("MAX_REQUESTS_PER_RUN", 60))
        self.spacing, self.timeout = spacing, timeout
        self._open = opener or urllib.request.urlopen
        self._sleep = sleep or time.sleep
        self._clock = clock or time.monotonic
        self._last = None
        self.requests = 0
        self.log = []                                   # (path without query, status): safe to print

    def __repr__(self):                                 # never let the key reach a log via repr
        return "<bdl Client requests=%d/%d>" % (self.requests, self.max_requests)

    def get(self, path):
        clean = path.split("?", 1)[0]
        if any(clean.rstrip("/").endswith(r) or (r + "/") in clean for r in REFUSED):
            raise ValueError("refused endpoint on the NEVER list: %s" % clean)
        backoff = 2.0
        for attempt in range(3):
            if self.requests >= self.max_requests:
                raise CapReached("per-run request cap of %d reached" % self.max_requests)
            if self._last is not None:
                wait = self.spacing - (self._clock() - self._last)
                if wait > 0:
                    self._sleep(wait)
            self._last = self._clock()
            self.requests += 1
            req = urllib.request.Request(BASE + path, headers={"Authorization": self._key})
            try:
                with self._open(req, timeout=self.timeout) as r:
                    status, body = r.getcode(), r.read()
                self.log.append((clean, status))
                return status, json.loads(body.decode("utf-8"))
            except urllib.error.HTTPError as e:
                self.log.append((clean, e.code))
                if e.code == 429 and attempt < 2:
                    ra = e.headers.get("Retry-After") if e.headers else None
                    self._sleep(float(ra) if ra and ra.replace(".", "", 1).isdigit() else backoff)
                    backoff *= 2
                    continue
                return e.code, None
            except Exception:
                self.log.append((clean, None))
                return None, None
        return 429, None

    def get_all(self, path, max_pages=5):
        """Follows cursor pagination; returns (status, rows). Stops on the first non-200."""
        rows, cursor = [], None
        for _ in range(max_pages):
            sep = "&" if "?" in path else "?"
            status, data = self.get(path + ("%scursor=%s" % (sep, cursor) if cursor else ""))
            if status != 200 or not data:
                return status, rows
            rows += data.get("data", [])
            cursor = (data.get("meta") or {}).get("next_cursor")
            if not cursor:
                return 200, rows
        return 200, rows
