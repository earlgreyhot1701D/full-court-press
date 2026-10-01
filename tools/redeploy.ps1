# redeploy.ps1 - the whole redeploy in one command (owner runs it; Windows PowerShell).
#
#   powershell -ExecutionPolicy Bypass -File tools\redeploy.ps1            # deploy + rebuild + golden
#   powershell -ExecutionPolicy Bypass -File tools\redeploy.ps1 -Record    # ...then record the demo video
#
# No secrets or account numbers live in this file: the deploy reuses the stack's current parameter
# values (read from CloudFormation), and the certificate is looked up by domain. Stops at the first
# failure and says which step.

param([switch]$Record)
$ErrorActionPreference = "Stop"
$env:AWS_PROFILE = "fcp"
$Nights = @("2026-09-21", "2026-09-22", "2026-09-23", "2026-09-24", "2026-09-27", "2026-09-29", "2026-09-30")

function Step($n, $text) { Write-Host ""; Write-Host "== $n. $text" -ForegroundColor Cyan }
function Check($what) { if ($LASTEXITCODE -ne 0) { Write-Host "FAILED at: $what (paste this to Claude)" -ForegroundColor Red; exit 1 } }

Step 1 "Build the Lambda bundle"
python tools/build_lambda.py; Check "build"

Step 2 "Deploy (reuses the stack's current parameters, domain included)"
$params = aws cloudformation describe-stacks --stack-name full-court-press --query "Stacks[0].Parameters" --output json | ConvertFrom-Json; Check "read stack parameters"
$overrides = @()
foreach ($p in $params) { if ($p.ParameterValue -and $p.ParameterValue -ne "****") { $overrides += ("{0}={1}" -f $p.ParameterKey, $p.ParameterValue) } }
if (-not ($overrides -match "^SiteDomain=fullcourtpress.lol$")) { Write-Host "SiteDomain missing from the stack parameters; stopping so the domain isn't dropped." -ForegroundColor Red; exit 1 }
sam deploy --stack-name full-court-press --capabilities CAPABILITY_IAM --no-confirm-changeset --no-fail-on-empty-changeset --parameter-overrides $overrides; Check "sam deploy"

Step 3 "Rebuild the nights, one at a time"
foreach ($n in $Nights) {
  ('{"nights": ["' + $n + '"]}') | Set-Content -Encoding ascii payload.json
  $r = aws lambda invoke --function-name fcp-hunter --cli-binary-format raw-in-base64-out --payload file://payload.json response.json | ConvertFrom-Json; Check "rebuild $n"
  if ($r.StatusCode -ne 200 -or $r.FunctionError) { Write-Host "FAILED rebuilding $n (paste response.json to Claude)" -ForegroundColor Red; exit 1 }
  Write-Host "  $n rebuilt"
}

Step 4 "Clear the CloudFront cache and wait for it"
$dist = aws cloudfront list-distributions --query "DistributionList.Items[?DomainName=='dfph64wiizg5i.cloudfront.net'].Id" --output text; Check "find distribution"
$inv = aws cloudfront create-invalidation --distribution-id $dist --paths "/*" --query "Invalidation.Id" --output text; Check "invalidate"
aws cloudfront wait invalidation-completed --distribution-id $dist --id $inv; Check "wait for invalidation"

Step 5 "Republish golden"
$bucket = aws cloudformation describe-stacks --stack-name full-court-press --query "Stacks[0].Outputs[?contains(OutputKey,'Bucket')].OutputValue" --output text; Check "find bucket"
$env:SITE_URL = "https://fullcourtpress.lol/"; $env:PYTHONPATH = "src"
python -m zine.publish_golden --bucket $bucket; Check "golden"

if ($Record) {
  Step 6 "Record the demo video (about 90 seconds, nothing opens on screen)"
  python tools/record_demo.py demo/demo_shots.json --out demo/demo.mp4; Check "record demo"
}

Write-Host ""; Write-Host "DONE. Tell Claude: redeployed" -ForegroundColor Green
