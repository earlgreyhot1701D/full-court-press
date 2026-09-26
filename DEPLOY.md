# Deploy runbook (Block 5)

Everything below except the AWS steps was built and tested on disk (Claude, Sep 26; 166 tests).
Kiro runs the AWS steps in one session. The owner approves the deploy and types her own email.

Rules that still hold: no IAM users or access keys; never read, print or log the BALLDONTLIE key
(it lives only in SSM `/full-court-press/bdl-api-key`); redact the account id in anything saved;
logs never contain prompts, model text, feed bodies or keys.

## 0. Cost allocation tag (Kiro checks, owner approves the change)
No record that `Project` was ever activated (OWNER-SETUP.md listed it as a Block 0 owner step; no LEDGER entry).
```
aws ce list-cost-allocation-tags --tag-keys Project
```
- `Status: Active`: nothing to do, note it in LEDGER.
- `Inactive`: propose, and on the owner's go run
  `aws ce update-cost-allocation-tags-status --cost-allocation-tags-status TagKey=Project,Status=Active`
- Not listed: the key has not appeared yet (it shows up to 24 hours after the first tagged resource).
  Deploy anyway, then check again tomorrow. Costs before activation are not tagged; the `fcp-project`
  budget reads $0 until then, and `fcp-polly` still works because it filters by service.

## 0b. Owner, before the session
- [ ] Optional, recommended: rerun the voices so the golden set publishes under the latest rules:
      `python -m zine.dev_render_live --fresh` (your terminal, `$env:PYTHONPATH="src"` and `$env:MODEL_ID=...` set).

## 1. Build the bundle (Kiro)
```
pip install -r requirements.txt
python tools/build_lambda.py
```
Do **not** run `sam build`: on Windows it installs Windows wheels and Pillow will not import in Lambda.
`build/lambda/` is what `CodeUri` points at.

## 2. Validate (Kiro)
```
sam validate --lint
```
Fix only what the linter flags in `template.yaml`. Report every change. Do not refactor other code.

## 3. Deploy (owner approves first)
```
sam deploy --guided --stack-name full-court-press --capabilities CAPABILITY_IAM --tags Project=full-court-press
```
Parameters: `AlertEmail` = owner's email (owner types it). Keep the defaults for the rest.
Save the outputs: `SiteUrl`, `BucketName`, `HunterName`, `RecapProfileArn`.

## 4. First run by hand (Kiro)
```
aws lambda invoke --function-name fcp-hunter response.json
```
`response.json` is the run summary: built game ids, failures (id + error type), model calls, audio count,
marker. Safe to paste. Then read the CloudWatch log group `/aws/lambda/fcp-hunter` for that run and confirm
it holds ids, counts and lock rules only.

Check specifically (unverified before deploy):
- The Lambda imports (Pillow, fonts, templates found). An `ImportError` or "templates/ not found" means the
  bundle step was skipped or `sam build` was used.
- Bedrock through `fcp-recap` works (a voice section kept, not every section dropped with an AccessDenied type).
- The games-by-date query: yesterday's games are in `built`, and a West Coast game is on the right night.

## 5. Publish the golden set (Kiro)
```
$env:PYTHONPATH="src"; python -m zine.publish_golden --bucket <BucketName>
```

## 6. CHECKPOINT 5 evidence (Kiro gathers, owner reviews)
- [ ] `SiteUrl` loads; `SiteUrl/golden/index.html` loads; phone width fine
- [ ] Direct S3 object URL returns AccessDenied
- [ ] `curl -I <SiteUrl>` shows CSP, HSTS, X-Content-Type-Options, X-Frame-Options, Referrer-Policy
- [ ] The morning schedule `fcp-morning` exists (6:15am Pacific)
- [ ] Budgets `fcp-project` and `fcp-polly` exist, OK state
- [ ] Cost allocation tag `Project` shows Active (step 0), with the date it was activated noted in LEDGER
- [ ] CloudWatch: ids, counts and lock rules only
- [ ] Next morning: the scheduled run published with nobody touching it

## Rollback
- Bad publish: S3 versioning is on; restore the previous version of the affected keys.
- Bad code: redeploy the previous commit's bundle.
- Runaway spend: disable the schedule `fcp-morning` (console or `aws scheduler update-schedule ... --state DISABLED`).
