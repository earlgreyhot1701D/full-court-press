"""Private cache of raw feed bodies and voice results, so a game can be rebuilt without calling
the feed or the model again. Stored under cache/ (never served; not a log)."""
import json


def put_raw(store, league, game_id, name, obj):
    store.put("cache/raw/%s/%s/%s.json" % (league, game_id, name), json.dumps(obj).encode("utf-8"), "application/json")


def get_raw(store, league, game_id, name):
    raw = store.get("cache/raw/%s/%s/%s.json" % (league, game_id, name))
    return json.loads(raw) if raw else None


def put_voices(store, league, game_id, results):
    """results: {(edition, voice): voice_run result or None}"""
    body = {"%s/%s" % k: v for k, v in results.items()}
    store.put("cache/voices/%s/%s.json" % (league, game_id), json.dumps(body, ensure_ascii=False).encode("utf-8"),
              "application/json")


def get_voices(store, league, game_id):
    raw = store.get("cache/voices/%s/%s.json" % (league, game_id))
    if not raw:
        return None
    return {tuple(k.split("/")): v for k, v in json.loads(raw).items()}
