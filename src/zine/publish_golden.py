"""Publish the golden set to the deployed bucket under site/golden/ (Req 11.2), through the same
site builder as live issues (Req 11.3). Run once after deploy, by Kiro or the owner, with AWS
credentials in that terminal. Voices come from the owner's saved live run
(out-golden/voice-results.json); a game with no saved result shows "writers' room passed".

    PYTHONPATH=src python -m zine.publish_golden --bucket <bucket name>      # to S3
    PYTHONPATH=src python -m zine.publish_golden --local out-publish         # to a folder, to look first
"""
import argparse
import json
import os

from zine import dev_render_golden, site_build
from zine.store import LocalStore, S3Store, publish


def saved_results():
    p = os.path.join(dev_render_golden.OUT, "voice-results.json")
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--bucket")
    g.add_argument("--local")
    a = ap.parse_args()
    saved = saved_results()
    result_fn = lambda f, ed, v: saved.get("%s/%s/%s" % (f["game_id"], ed, v))
    files, gotn = dev_render_golden.golden_files(result_fn, prefix="golden/")
    files.update(site_build.static_files())
    store = S3Store(a.bucket) if a.bucket else LocalStore(a.local)
    n = publish(store, files)
    kept = sum(1 for r in saved.values() for s in (r or {}).get("sections", {}).values() if s is not None)
    print("published %d files under site/golden/ . Game of the Night %s . voice sections kept %d" % (n, gotn, kept))


if __name__ == "__main__":
    main()
