"""Task 2.2: the API client and key reader, with the network and clock faked. No real calls."""
import io
import json
import urllib.error

import pytest

from zine import api_key
from zine.bdl_client import CapReached, Client

KEY = "TEST-KEY-not-real"


class Resp:
    def __init__(self, status, payload):
        self.status, self.body = status, json.dumps(payload).encode()
    def getcode(self): return self.status
    def read(self): return self.body
    def __enter__(self): return self
    def __exit__(self, *a): return False


def opener_from(script):
    seen = []
    def op(req, timeout):
        seen.append((req.full_url, dict(req.header_items()), timeout))
        item = script.pop(0)
        if isinstance(item, Exception):
            raise item
        return item
    return op, seen


def http_error(code, retry_after=None):
    hdrs = {"Retry-After": retry_after} if retry_after else {}
    return urllib.error.HTTPError("u", code, "x", hdrs, io.BytesIO(b""))


def fake_clock():
    t = [0.0]
    return (lambda: t[0]), (lambda s: t.__setitem__(0, t[0] + s)), t


def test_auth_header_is_the_bare_key_and_timeout_is_set():
    op, seen = opener_from([Resp(200, {"data": []})])
    clock, sleep, _ = fake_clock()
    c = Client(KEY, opener=op, sleep=sleep, clock=clock)
    assert c.get("/wnba/v1/games?dates[]=2026-09-21") == (200, {"data": []})
    url, headers, timeout = seen[0]
    assert headers["Authorization"] == KEY and timeout == 10


def test_requests_are_spaced_at_least_one_second():
    op, _ = opener_from([Resp(200, {}), Resp(200, {})])
    clock, sleep, t = fake_clock()
    c = Client(KEY, opener=op, sleep=sleep, clock=clock)
    c.get("/wnba/v1/games"); c.get("/wnba/v1/teams")
    assert t[0] >= 1.0


def test_never_list_endpoints_are_refused_before_any_request():
    op, seen = opener_from([])
    c = Client(KEY, opener=op)
    for path in ("/wnba/v1/odds?game_ids[]=1", "/wnba/v1/odds/player_props?game_id=1",
                 "/wnba/v1/player_injuries", "/wnba/v1/player_stats?game_ids[]=1"):
        with pytest.raises(ValueError):
            c.get(path)
    assert seen == []


def test_per_run_cap_stops_requests():
    op, _ = opener_from([Resp(200, {})] * 3)
    clock, sleep, _ = fake_clock()
    c = Client(KEY, max_requests=2, opener=op, sleep=sleep, clock=clock)
    c.get("/wnba/v1/teams"); c.get("/wnba/v1/teams")
    with pytest.raises(CapReached):
        c.get("/wnba/v1/teams")


def test_429_backs_off_and_retries_then_succeeds():
    op, seen = opener_from([http_error(429, "3"), Resp(200, {"ok": 1})])
    clock, sleep, t = fake_clock()
    c = Client(KEY, opener=op, sleep=sleep, clock=clock)
    assert c.get("/wnba/v1/teams") == (200, {"ok": 1})
    assert len(seen) == 2 and t[0] >= 3


def test_401_is_not_retried():
    op, seen = opener_from([http_error(401)])
    clock, sleep, _ = fake_clock()
    c = Client(KEY, opener=op, sleep=sleep, clock=clock)
    assert c.get("/wnba/v1/standings") == (401, None)
    assert len(seen) == 1


def test_network_failure_returns_none_and_the_key_appears_nowhere():
    op, _ = opener_from([OSError("boom")])
    c = Client(KEY, opener=op, sleep=lambda s: None)
    assert c.get("/wnba/v1/teams") == (None, None)
    assert KEY not in repr(c) and KEY not in json.dumps(c.log)


def test_cursor_pagination_collects_every_page():
    op, seen = opener_from([Resp(200, {"data": [1, 2], "meta": {"next_cursor": 9}}),
                            Resp(200, {"data": [3], "meta": {}})])
    c = Client(KEY, opener=op, sleep=lambda s: None)
    assert c.get_all("/wnba/v1/players?team_ids[]=3") == (200, [1, 2, 3])
    assert seen[1][0].endswith("&cursor=9")


# ---- api_key ------------------------------------------------------------------------

class FakeSSM:
    def __init__(self, value=None, fail=False): self.value, self.fail, self.calls = value, fail, 0
    def get_parameter(self, Name, WithDecryption):
        self.calls += 1
        if self.fail: raise RuntimeError("AccessDenied: " + KEY)     # a leaky error message
        return {"Parameter": {"Value": self.value}}


def test_env_var_wins_and_is_cached(monkeypatch):
    api_key._reset_for_tests()
    monkeypatch.setenv("BDL_API_KEY", KEY)
    ssm = FakeSSM("other")
    assert api_key.get_key(ssm) == KEY and ssm.calls == 0


def test_ssm_is_read_once_then_cached(monkeypatch):
    api_key._reset_for_tests()
    monkeypatch.delenv("BDL_API_KEY", raising=False)
    ssm = FakeSSM(KEY)
    assert api_key.get_key(ssm) == KEY and api_key.get_key(ssm) == KEY and ssm.calls == 1


def test_a_failure_never_carries_the_key_in_its_message(monkeypatch):
    api_key._reset_for_tests()
    monkeypatch.delenv("BDL_API_KEY", raising=False)
    with pytest.raises(api_key.KeyUnavailable) as e:
        api_key.get_key(FakeSSM(fail=True))
    assert KEY not in str(e.value)
