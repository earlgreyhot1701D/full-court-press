"""Local dry run of the hunter (Req 1.6): golden fixtures as the feed, no model (every voice
section passes), no Polly, no S3. Output lands in ./out-dry/<site files> for a look.

    PYTHONPATH=src python -m zine.dry_run --date 2026-09-22     # the run date (Pacific); builds the night before
"""
import argparse
import json
import os
import shutil
from datetime import date

from zine import hunter
from zine.fixture_feed import FakeBDL
from zine.paths import ROOT
from zine.store import LocalStore

OUT = os.path.join(ROOT, "out-dry")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="accepted for the spec's wording; this module only dry-runs")
    ap.add_argument("--date", required=True, help="run date, Pacific, YYYY-MM-DD")
    a = ap.parse_args()
    shutil.rmtree(OUT, ignore_errors=True)
    s = hunter.run(LocalStore(OUT), FakeBDL(), lambda system, messages: None, None, date.fromisoformat(a.date),
                   {"MAX_MODEL_CALLS_PER_RUN": "0", "MAX_AUDIO_PER_RUN": "0", "LEAGUES": "wnba"})
    print(json.dumps(s, indent=1))
    print("Open out-dry/site/index.html")


if __name__ == "__main__":
    main()
