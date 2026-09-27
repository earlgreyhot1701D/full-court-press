Kiro: third follow-up. Thank you for stopping on 25079. Findings (LEDGER "Sep 24 rebuild"):
- 5 games on Eastern Sep 24 is correct. Claude's "expect 3" was stale.
- 25079's UndefinedError was a template gap (a missing quarters section), fixed and tested on disk.
DO NOT edit application code. Propose each AWS-changing step and wait for the owner's go.

1. Rebuild and redeploy (owner's go):  python tools/build_lambda.py ; sam deploy
2. Re-invoke Eastern Sep 24 (owner's go), payload {"nights": ["2026-09-24"]}.
   Expect: built = 25079, 25080, 25081, 25082, 25083; failed = []; stray = 0.
   The other four reuse their cached voices, so new model calls should be only 25079's (up to 8).
   If failed is not empty, STOP and report response.json (the entry now includes a detail field).
3. Then one invoke each for 2026-09-23, 2026-09-22, 2026-09-21. Any count of games is fine;
   stop only on failed entries or stray > 0. Report each response.json.
4. Continue DEPLOY.md step 5 (publish golden) and step 6 (checkpoint evidence, including the Project
   cost allocation tag and the site URL on a phone).

Log in BUILD-LOG.md as (Kiro) entries.
