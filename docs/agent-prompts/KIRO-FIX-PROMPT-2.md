Kiro: second follow-up. Your probe settled it (thank you): the API files games by UTC date, so
00:00Z and 02:00Z Sep 25 are Sep 24 evening games in US Eastern time. The first empty run was
correct; Claude's "midnight" fix was wrong and put 25081 under Sep 25. Fixed on disk; see LEDGER
"Date model settled by the probe". DO NOT edit application code.

Propose each AWS-changing step and wait for the owner's go.

1. Delete your temp files: _datecheck.py, _datecheck.json, _stream.txt, _hunter_log.txt, _probe.json, payload.json.
2. Rebuild and redeploy (owner's go):
     python tools/build_lambda.py
     sam deploy
3. Remove the wrongly dated publish (owner's go). Only these keys:
     aws s3 rm s3://<BucketName>/site/wnba/2026-09-25/ --recursive --profile fcp --region us-east-1
     aws s3 rm s3://<BucketName>/state/slates/wnba/2026-09-25.json --profile fcp --region us-east-1
   Do not touch cache/ (25081's voices are reused).
4. Rebuild Eastern Sep 24 (owner's go): payload.json = {"nights": ["2026-09-24"]}
     aws lambda invoke --function-name fcp-hunter --cli-binary-format raw-in-base64-out --payload fileb://payload.json response.json --profile fcp --region us-east-1
   Expect: built = 25081, 25082, 25083; nights["2026-09-24"].matched = 3; stray = 0; failed = [].
   If not, STOP and report response.json.
5. Then one invoke each for 2026-09-23, then 2026-09-22, then 2026-09-21. Report each response.json.
6. Continue DEPLOY.md step 5 (publish golden) and step 6 (checkpoint evidence, including the
   Project cost allocation tag and the site URL on a phone).

Log in BUILD-LOG.md as (Kiro) entries.
