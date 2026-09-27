"""Local render of the golden set through the real site builder, to ./out-golden/ (gitignored).

out-golden/ is laid out exactly like the deployed site root, static files included, so what you
open locally is what CloudFront serves. Voices come from `result_fn`; the default is Claude's
labeled stand-ins for 25071 (fixtures/voice_standins/) and "writers' room passed" everywhere else.
dev_render_live passes real Haiku results instead.

Run: PYTHONPATH=src python -m zine.dev_render_golden
"""
import glob
import json
import os
import shutil

from zine import site_build, voice_run
from zine.facts import build_facts
from zine.game_of_night import pick
from zine.paths import ROOT
from zine.store import LocalStore
from zine.voices import VOICE_ORDER

GOLDEN = os.path.join(ROOT, "fixtures", "golden")
OUT = os.path.join(ROOT, "out-golden")
STANDINS = os.path.join(ROOT, "fixtures", "voice_standins")
LABEL = "The golden set"


def load_all():
    standings = json.load(open(os.path.join(GOLDEN, "standings.json")))["data"]
    out = []
    for g in sorted(glob.glob(os.path.join(GOLDEN, "[0-9]*"))):
        game = json.load(open(os.path.join(g, "game.json")))["data"]
        plays = json.load(open(os.path.join(g, "plays.json")))["data"]
        rl = {p.rsplit("_", 1)[1][:-5]: json.load(open(p))["data"] for p in glob.glob(os.path.join(g, "roster_*.json"))}
        out.append(build_facts(game, plays, rl, standings))
    return out


def standin_result(f, edition, voice):
    p = os.path.join(STANDINS, "%s.json" % f["game_id"])
    if not os.path.exists(p):
        return None
    answer = json.load(open(p, encoding="utf-8")).get(edition, {}).get(voice)
    if answer is None:
        return None
    return voice_run.run(lambda system, messages: dict(answer), f, voice, edition)


def golden_files(result_fn, prefix=""):
    """Every file of the golden site. Used locally (prefix "") and by publish_golden ("golden/")."""
    facts = load_all()
    voiced = {f["game_id"]: {(t["abbrev"], v): result_fn(f, t["abbrev"], v) for t in (f["home"], f["away"])
                             for v in VOICE_ORDER} for f in facts}
    gotn = pick(facts, eligible=site_build.featurable(facts, voiced))  # same rule as the morning run
    rows = [site_build.slate_row(f, gotn, prefix, results=voiced[f["game_id"]]) for f in facts]
    files = {}
    for f in facts:
        files.update(site_build.issue_files(f, voiced[f["game_id"]], gotn, rows, prefix=prefix))
    nights = {}
    for r in rows:
        nights.setdefault(r["date_local"], []).append(r)
    files.update(site_build.front_files(nights, prefix=prefix, label=LABEL, front_rows=rows))
    return files, gotn


def main(result_fn=None):
    site_build.GOLDEN_AT = ""  # locally the golden set is the site root
    files, gotn = golden_files(result_fn or standin_result)
    files.update(site_build.static_files())
    keep = os.path.join(OUT, "voice-results.json")
    saved = open(keep, "rb").read() if os.path.exists(keep) else None
    for sub in ("game", "wnba", "about", "archive", "team", "data", "static", "cards"):
        shutil.rmtree(os.path.join(OUT, sub), ignore_errors=True)  # drop the old layout
    store = LocalStore(OUT)
    for path, (body, _ctype) in files.items():
        store.put(path, body)
    if saved is not None:
        store.put("voice-results.json", saved)
    print("Game of the Night: %s . wrote %d files to out-golden/" % (gotn, len(files)))


if __name__ == "__main__":
    main()
