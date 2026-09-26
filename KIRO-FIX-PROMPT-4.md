Kiro: fourth follow-up. Your read was right: the forced rebuild skipped a night it thought was done.
Claude's bug (the slate recorded 25079 as built although its page failed). Fixed on disk.
DO NOT edit application code. Owner has approved the sequence below as one go; no need to ask between steps.

1. python tools/build_lambda.py ; sam deploy
2. Invoke with {"nights": ["2026-09-24"]}, then {"nights": ["2026-09-23"]}, then {"nights": ["2026-09-22"]},
   then {"nights": ["2026-09-21"]}, one at a time.
   STOP only if a run has a non-empty `failed` list or `stray` > 0. Game counts and call counts are
   not stop conditions. Report all four summaries at the end (from CloudWatch if response.json is flaky).
3. Publish golden: $env:PYTHONPATH="src"; python -m zine.publish_golden --bucket <BucketName>
4. DEPLOY.md step 6 checkpoint evidence, including the Project cost allocation tag. Report the site URL.

Log in BUILD-LOG.md as (Kiro) entries.
