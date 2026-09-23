# Findings ledger

One entry per block, per spike question, and before any code is discarded. Keep wrong versions: the correction is the interesting part.

## Entry template
```
### <date> . Block <n> . <short title>
Question:     <what we needed to know>
Answer:       <yes / no / PASS / FAIL, with evidence>
Cost:         <time, attempts>
Disposition:  <discard | promote | shelve (branch + hash)>
Changes PRD?: <no | yes: what>
```

## Entries

### 2026-09-20 . Block 0 . Compliance gate: data source
Question:     Can we pull WNBA box scores from ESPN's site API on a schedule and feed them to a model?
Answer:       No. The Disney/ESPN Terms of Use prohibit accessing or extracting content "using a robot, spider, script, or other automated means, including... for the purposes of creating or developing any AI Tool, data mining or web scraping", license content for "personal, noncommercial use only", and bar building a dataset from it. www.espn.com/robots.txt disallows */boxscore? and */playbyplay? for all user agents and blocks several AI crawlers outright. site.api.espn.com returns Access Denied for robots.txt, so there is no permission to rely on there either.
Replacement:  BALLDONTLIE. Terms Section 6 expressly permits use, caching, storage, publishing, derivative works and "artificial intelligence and machine-learning training or outputs", with no attribution required. Restrictions we must respect: do not build a product that competes with BALLDONTLIE, do not resell raw data, do not imply official league or BALLDONTLIE endorsement.
Cost:         Free tier covers games. Player stats need ALL-STAR ($9.99/mo per sport). Standings and plays need GOAT ($39.99/mo), so both are STUBs.
Disposition:  promote (spec updated: tech.md, design.md, requirements 2/3/9, tasks 0.2/0.4/2.x/5.1, PRD)
Changes PRD?: yes. Data source, quarter-based game flow, STUBs for runs and standings, API key in SSM, data cost line.

### 2026-09-23 . Block 0 . 0.1 Repo walls
Question:     Is the repo initialized with the spike wall (pre-commit hook) actually firing?
Answer:       PASS. git init on master. "kickoff" commit fa4dea9 with steering, spec, PRD.md, LEDGER.md, design/, .githooks/pre-commit, .gitignore, and .kiro/settings/mcp.json (owner asked mcp.json be committed; contains no secret and no account id). core.hooksPath set to .githooks. Hook verified live: on a spike/* branch, committing a file outside spike/ was rejected ("spike branch may only touch spike/ and LEDGER.md"); committing spike/THROWAWAY was allowed. Git for Windows bash 5.3.9 runs the hook.
Hook rejects on a spike/* branch: any staged path not under spike/ and not LEDGER.md; plus, on any branch, staged dependency manifests under spike/ (requirements*.txt, package.json, lockfiles, Pipfile, pyproject.toml) and staged tests/README under spike/ (test_, _test.py, README).
Cost:         ~10 min, 1 attempt.
Disposition:  spike/THROWAWAY lives on branch spike/hook-check (deleted at 0.8). Repo walls on master are permanent.
Changes PRD?: no.

### 2026-09-23 . Block 0 . 0.3c Connection proof
Question:     Can the coding agent, via the fcp profile CLI, prove it made real AWS calls (not a human in the console)?
Answer:       PASS (agent side). aws sts get-caller-identity --profile fcp returned identity (arn ...:root, account redacted). Created S3 bucket fcp-proof-7y2983ri in us-east-1, tagged Project=full-court-press (verified via get-bucket-tagging and head-bucket). Transcript saved to proof/transcript-0-3.txt with account id redacted to **** (verified absent). CloudTrail capture (0.3d/0.3e) is owner's step.
First AWS call timestamp (for CloudTrail search): 2026-09-23T23:09:14.072Z UTC (sts get-caller-identity).
Cost:         ~10 min, 1 attempt. Bucket empty, deleted at 0.8.
Disposition:  bucket fcp-proof-7y2983ri to be deleted at 0.8. proof/ is gitignored.
Changes PRD?: no.

### 2026-09-23 . Block 0 . 0.3 disposition (scope change by owner)
Question:     Does 0.3 pass for Block 0 without the CloudTrail/console capture?
Answer:       PASS on three layers: (1) aws login browser sign-in under profile fcp; (2) .kiro/settings/mcp.json committed with AWS_MCP_PROXY_PROFILES=fcp and an MCP tool call succeeded earlier; (3) CLI transcript proof/transcript-0-3.txt with account id redacted. Two layers DEFERRED out of Block 0 by owner decision: 0.3d CloudTrail event capture and 0.3e console screenshot. Rationale: CloudTrail retains 90 days and AWS has not requested it. CHECKPOINT 0 no longer waits on the owner's capture.
Cost:         n/a (scope change).
Disposition:  0.3d/0.3e deferred; can be captured later from CloudTrail history if needed.
Changes PRD?: no (spec task 0.3 acceptance relaxed for Block 0; owner to reconcile tasks.md if desired).

### 2026-09-23 . Block 0 . Build log rule added
Question:     n/a (owner standing rule).
Answer:       Added a "Build log" section to guardrails.md: maintain BUILD-LOG.md at repo root, append one entry per task before reporting, never rewrite entries, public-safe (no account id, ARN, secret, prompt, or model output). Backfilled 0.1 and 0.3c entries. Note: BLOCK-0-PROMPT.md referenced by owner does not exist in the repo (only KIRO-KICKOFF-PROMPT.md, which is the older prompt); acted on the owner message directly and defined the entry format since no format was written in the repo.
Cost:         n/a.
Disposition:  permanent (guardrails.md + BUILD-LOG.md on master).
Changes PRD?: no.
