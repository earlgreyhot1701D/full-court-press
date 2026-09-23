# Tech

## Stack (verify versions before use, do not assume)
- Python on AWS Lambda. Use the newest Python runtime Lambda lists as supported at build time; record it in the Block 0 ledger entry.
- AWS SAM for infrastructure (`template.yaml`). One stack.
- EventBridge Scheduler: one morning schedule (Pacific time) that invokes the hunter.
- S3: one private bucket, prefixes `raw/`, `facts/`, `site/`, `state/`. Versioning on.
- CloudFront in front of `site/` with Origin Access Control. Bucket is never public.
- Amazon Bedrock Runtime, Converse API, via boto3. `MODEL_ID` holds the ARN of the tagged application inference profile `fcp-recap` (for billing by project), never a bare model ID. Candidate: Claude Haiku 4.5. Block 0 confirms its lifecycle status is ACTIVE with `ListFoundationModels`. Do not hardcode a model ID anywhere else.
- Jinja2 with `autoescape=True` for all HTML rendering.
- Pillow for the share card PNG.
- Amazon Polly `SynthesizeSpeech`, **neural** engine, MP3 output, for the ~10 second audio recap. Voice from env var `POLLY_VOICE`. Owner shortlist: Danielle or Ruth (both neural en-US). Tiffany was the owner's first pick but is generative-only, and the generative engine is NEVER here, so Tiffany is out. Engine from `POLLY_ENGINE` (default `neural`). Same region as Bedrock, and it must be a region Polly supports.
- PDF: no server-side PDF. The printable foldable issue is the browser's own print, using `static/print.css`. Server-built PDFs are a STUB.
- Standard library `urllib.request` (or `requests` only if Block 0 shows a need) for HTTP.
- Frontend: static HTML + CSS + one small vanilla JS file. No framework, no build step.

## Agent connection to AWS
Use the **Agent Toolkit for AWS** (`https://github.com/aws/agent-toolkit-for-aws`, setup-instructions/setup.md). It installs AWS CLI v2, the AWS MCP server wired into Kiro, and AWS agent skills, and it authenticates with `aws login` in the browser: temporary credentials, 12 hours, renewable for 90 days. No access keys, no long-lived secret on disk.
- Profile name: `fcp` (used in every AWS CLI command and in Kiro's MCP config as `AWS_MCP_PROXY_PROFILES`).
- Region: **us-east-1**. The toolkit uses us-east-1 internally, and it is a region that supports both Bedrock and Polly neural. Keep the whole stack there.
- The toolkit adds its own AWS rules to `.kiro/steering/`. Those are additional, not a replacement: `guardrails.md` still wins on any conflict, and if they conflict, stop and report.
- If the toolkit cannot be installed, fall back to an IAM user named `fcp-kiro-agent` with console access disabled and an access key (see OWNER-SETUP.md), and record the fallback in LEDGER.md.

## Dependencies
Only: `boto3` (provided by Lambda, do not bundle unless Block 0 finds a reason), `jinja2`, `Pillow`. Anything else needs the owner's approval first. No vendored modules.

## Data source: BALLDONTLIE
Chosen Sep 20 2026 after the compliance gate ruled out ESPN (see LEDGER.md). BALLDONTLIE's terms Section 6 expressly permit caching, publishing, derivative works and AI outputs, with no attribution required.
- Base: `https://api.balldontlie.io`. Auth header on every request: `Authorization: <api key>` (no "Bearer").
- Games (schedule + final scores + per-quarter scores): `GET /wnba/v1/games?dates[]=YYYY-MM-DD`
- Player stats per game: `GET /wnba/v1/player_stats?game_ids[]=<id>`
- Standings: `GET /wnba/v1/standings` . Play-by-play: `GET /wnba/v1/plays?game_id=<id>`
- NBA STUB swaps `wnba` for `nba` in the path.
- Pagination is cursor based: `meta.next_cursor`, `per_page` max 100.
- Tiers (confirm per sport in Block 0; the published table is for NBA): Free = teams, players, games. ALL-STAR $9.99/mo per sport = game player stats. GOAT $39.99/mo = box scores, standings, plays, odds. A 48-hour GOAT trial exists per sport.
- **Never read** the odds or player-prop endpoints at any tier.
- Outbound limits: honor the tier's requests/min (Free 5, ALL-STAR 60), at least 1 second between requests anyway, max 60 requests per run, 10 second timeout, and back off on HTTP 429.

## Secret: the API key
- Stored in SSM Parameter Store as a SecureString at `/full-court-press/bdl-api-key`. Never in the repo, never in env vars checked into git, never printed.
- Lambda reads it at cold start with `ssm:GetParameter` (+ `kms:Decrypt` on the default key) and holds it in memory only.
- Local dev reads it from the shell env var `BDL_API_KEY`, which stays out of git via `.gitignore`.
- Logs never contain the key or any request URL that carries it in a header dump.

## Environment variables (Lambda)
`LEAGUES` (default `wnba`), `MODEL_ID`, `BUCKET`, `SITE_PREFIX`, `BDL_KEY_PARAM` (default `/full-court-press/bdl-api-key`), `MAX_REQUESTS_PER_RUN`, `MAX_MODEL_CALLS_PER_RUN` (default 60), `POLLY_VOICE`, `POLLY_ENGINE` (default `neural`), `MAX_AUDIO_PER_RUN` (default 30), `LOG_LEVEL` (default `INFO`).
Tag every resource `Project=full-court-press`. The only secret is the BALLDONTLIE API key, in SSM (above). If a task seems to need another secret, stop and report.

## Logging
- `logging` at INFO. Set `boto3`, `botocore`, `urllib3` loggers to WARNING at module load.
- Log: game ids, dates, counts, fact-lock pass/fail with the failing token, timings.
- Never log: prompts, model output text, raw feed bodies, AWS account ids.

## Local dev
- `python -m pytest` for Working-tier tests
- `python -m zine.hunter --date YYYY-MM-DD --dry-run` renders to `./out/` from cached raw JSON without calling S3 or Bedrock (mock voice)
