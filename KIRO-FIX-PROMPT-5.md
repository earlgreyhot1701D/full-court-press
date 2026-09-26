Kiro: fifth follow-up (owner approves the whole sequence; no need to ask between steps).
Claude added stricter voice rules that re-check saved voices at every render (no model calls), and a
line on the page explaining why a voice section is missing. DO NOT edit application code.

1. python tools/build_lambda.py ; sam deploy
2. Invoke one at a time: {"nights": ["2026-09-24"]}, {"nights": ["2026-09-23"]}, {"nights": ["2026-09-22"]}, {"nights": ["2026-09-21"]}.
   Expect model_calls 0 (voices are cached). Stop only on a non-empty `failed` or stray > 0.
3. Republish golden: $env:PYTHONPATH="src"; python -m zine.publish_golden --bucket <BucketName>
4. Spot check on the live site: one issue page with a missing recap shows the new "Our AI writer's draft
   didn't match..." line and its link to About works.
Report the four summaries (from CloudWatch) and the spot check. Log in BUILD-LOG.md as (Kiro) entries.
