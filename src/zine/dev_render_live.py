"""Local dev run of the real voices (task 3.5, before deploy). Owner runs it in her own terminal,
because the AWS login lives there. Nothing is published: output goes to ./out-golden/ (gitignored).

    cd C:\\Users\\corde\\projects\\full-court-press
    $env:PYTHONPATH="src"
    $env:MODEL_ID="us.anthropic.claude-haiku-4-5-20251001-v1:0"
    python -m zine.dev_render_live            # calls Haiku for anything not already saved
    python -m zine.dev_render_live --fresh    # ignores saved results and calls again

5 golden games x 2 editions x 2 voices = 20 results, at most 2 calls each, capped at 40 calls.
Results are saved to out-golden/voice-results.json so re-rendering costs nothing. That file holds
the model's text (it is page content, like the HTML), stays local, and is never logged.
The summary printed below carries only game, edition, voice, calls and lock rules: no model text.
"""
import json
import os
import sys

from zine import dev_render_golden, voice_client, voice_run

SAVED = os.path.join(dev_render_golden.OUT, "voice-results.json")
MAX_CALLS = 40


def main():
    if not os.environ.get("MODEL_ID"):
        sys.exit("Set MODEL_ID first (see the top of this file).")
    fresh = "--fresh" in sys.argv
    saved = {}
    if os.path.exists(SAVED) and not fresh:
        saved = json.load(open(SAVED, encoding="utf-8"))
    budget = voice_run.CallBudget(MAX_CALLS)
    print("Starting. Each line below is one page's voice; about 5 to 10 seconds each.", flush=True)
    summary = []

    def result_fn(f, edition, voice):
        key = "%s/%s/%s" % (f["game_id"], edition, voice)
        if key not in saved:
            print("calling Haiku: %s ..." % key, end=" ", flush=True)
            saved[key] = voice_run.run(voice_client.write, f, voice, edition, budget)
            print("done (%d call%s)" % (saved[key]["calls"], "" if saved[key]["calls"] == 1 else "s"), flush=True)
            os.makedirs(os.path.dirname(SAVED), exist_ok=True)  # save as we go: Ctrl+C loses nothing
            json.dump(saved, open(SAVED, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        r = saved[key]
        kept = [s for s, v in r["sections"].items() if v is not None]
        dropped = [s for s, v in r["sections"].items() if v is None]
        rules = sorted({"%s:%s" % (sec, v["rule"]) for e in r["log"] for sec, v in e.get("sections", {}).items()
                        if isinstance(v, dict)})
        errors = sorted({e["error"] for e in r["log"] if "error" in e})
        summary.append((key, r["calls"], len(kept), ",".join(dropped) or "-", " ".join(rules) or "-",
                        ",".join(errors) or "-"))
        return r

    dev_render_golden.main(result_fn)
    os.makedirs(os.path.dirname(SAVED), exist_ok=True)
    json.dump(saved, open(SAVED, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    print("\n%-26s %5s %5s  %-28s %-40s %s" % ("game/edition/voice", "calls", "kept", "dropped", "lock failures (any attempt)", "errors"))
    for row in summary:
        print("%-26s %5d %5d  %-28s %-40s %s" % row)
    total = sum(r[2] for r in summary)
    print("\nSections kept: %d of %d . model calls this run: %d of %d allowed"
          % (total, 4 * len(summary), MAX_CALLS - budget.left, MAX_CALLS))
    print("Open out-golden\\index.html in your browser.")


if __name__ == "__main__":
    main()
