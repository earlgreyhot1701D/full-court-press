Kiro: follow-up to the first deployed run. Claude diagnosed and fixed the date matching on disk
(see the LEDGER entry "First deployed run built nothing"). The marker is not the cause.

Do these in order. Propose each AWS-changing step and wait for the owner's go.

1. Probe (read-only), key in the environment for this one process only, never printed:
   $env:BDL_API_KEY = (aws ssm get-parameter --name "/full-court-press/bdl-api-key" --with-decryption --query "Parameter.Value" --output text --profile fcp --region us-east-1).Trim()
   python tools/probe_game_dates.py > _probe.json
   $env:BDL_API_KEY = $null
   Paste _probe.json in your report (ids, dates and status only; no key, no bodies).
2. Delete your temp files: _datecheck.py, _datecheck.json, _stream.txt, _hunter_log.txt, _probe.json (after reporting).
3. `git pull` is not needed (same folder). Rebuild the bundle: python tools/build_lambda.py
4. Redeploy (owner's go): sam deploy   (the guided run saved samconfig.toml; same stack and parameters)
5. Recover Sep 25 (owner's go). Write payload.json containing {"nights": ["2026-09-25"]} and run:
   aws lambda invoke --function-name fcp-hunter --cli-binary-format raw-in-base64-out --payload fileb://payload.json response.json --profile fcp --region us-east-1
   Report response.json. Expect: built has 3 game ids, nights["2026-09-25"] matched 3, model_calls > 0.
   If matched is still 0, STOP and report the nights block and the probe output. Do not edit code.
6. If step 5 passed: repeat step 5 for 2026-09-24, then 2026-09-23, then 2026-09-22, one invoke each
   (a 4-game night can use up to 32 model calls; one night per invoke stays under the 60-call cap).
7. Then continue DEPLOY.md from step 5 (publish golden) and step 6 (checkpoint evidence).

Log in BUILD-LOG.md as (Kiro) entries. DO NOT edit application code.
