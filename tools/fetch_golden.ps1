# Fetch the golden set. Run from the full-court-press folder:
#   powershell -ExecutionPolicy Bypass -File tools\fetch_golden.ps1
# The key goes from SSM into an environment variable for this one process and is
# removed afterwards. It is never printed and never written to disk.
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
$env:BDL_API_KEY = (aws ssm get-parameter --name "/full-court-press/bdl-api-key" `
  --with-decryption --query "Parameter.Value" --output text `
  --profile fcp --region us-east-1).Trim()
try {
  python tools\fetch_golden.py
} finally {
  Remove-Item Env:\BDL_API_KEY -ErrorAction SilentlyContinue
}
Get-Content fixtures\golden\FETCH-REPORT.txt
