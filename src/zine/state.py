"""Run state, private (never under site/): the last-run marker, each night's slate rows, and the
standings snapshot used to report movers. All JSON, all deterministic, no model text."""
import json

MARKER = "state/last_run.json"


def _get(store, key, default):
    raw = store.get(key)
    return json.loads(raw) if raw else default


def _put(store, key, obj):
    store.put(key, json.dumps(obj, sort_keys=True).encode("utf-8"), "application/json")


def read_marker(store):
    return _get(store, MARKER, {})


def write_marker(store, marker):
    _put(store, MARKER, marker)


def night_key(league, date):
    return "state/slates/%s/%s.json" % (league, date)


def save_night(store, league, date, rows):
    _put(store, night_key(league, date), rows)


def load_night(store, league, date):
    return _get(store, night_key(league, date), [])


def nights(store, league):
    out = {}
    for k in store.keys("state/slates/%s/" % league):
        date = k.rsplit("/", 1)[1][:-5]
        out[date] = _get(store, k, [])
    return out


def read_standings(store, league):
    return _get(store, "state/standings/%s.json" % league, {})


def write_standings(store, league, ranks):
    _put(store, "state/standings/%s.json" % league, ranks)
