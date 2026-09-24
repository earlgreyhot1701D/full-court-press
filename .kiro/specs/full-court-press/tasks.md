# Implementation Plan: Full Court Press

> **OPEN (Sep 19):** palette, name and team color are decided. Final OK on the issue sections as mocked (Req 5, 7, 8, 9) is still pending. Do not start Block 1 until this banner is removed.

Blocks run in order. Each block ends with a CHECKPOINT task. Every task in the next block depends on the previous checkpoint. Record PASS or FAIL with evidence in the checkpoint summary and in `LEDGER.md`. Guardrails in `.kiro/steering/guardrails.md` apply to every task. Each task names its tier. DO NOT refactor other code. Propose first, wait for owner approval, then implement.

Every checkpoint also answers: is anything from `spike/` still in use? If yes, stop and report.

## Block 0: Spikes (Tier: Spike. Disposition: discard, findings to LEDGER.md)
Tier: Spike. No tests, no pinning, no sync scripts, no README inside `spike/`, no abstractions, nothing outside `spike/`. Answer the question, record it, stop. The code is kept in the repo afterwards; "discard" means not promoted, not deleted.

- [ ] 0.1 Repo walls
  - `git init`, commit steering + spec + PRD as "kickoff"
  - `git config core.hooksPath .githooks` (hook file is provided; do not edit it)
  - Create `spike/` with a `THROWAWAY` marker file, `LEDGER.md` with the entry template
  - _Requirements: 12_
- [ ] 0.2 Compliance gate: DONE Sep 20 2026, recorded in LEDGER.md
  - ESPN ruled out (terms bar automated access and AI use; robots.txt disallows box score and play-by-play). BALLDONTLIE chosen: Section 6 permits caching, publishing, derivative works and AI outputs. Kiro does not redo this; read the ledger entry and move on.
  - _Requirements: 2_
- [ ] 0.3 Coding agent connection proof (five layers, see design.md "Connection proof")
  - 0.3a Owner installs the Agent Toolkit for AWS by following `https://raw.githubusercontent.com/aws/agent-toolkit-for-aws/refs/heads/main/setup-instructions/setup.md`. Profile `fcp`, region `us-east-1`. Auth is `aws login` in the browser, no access keys. Owner screenshots the successful sign-in and the toolkit's skill list.
  - 0.3a-fallback If the toolkit will not install, create the IAM user `fcp-kiro-agent` with console access disabled and one access key (OWNER-SETUP.md), and note the fallback in LEDGER.md.
  - 0.3b Kiro's MCP config carries `"AWS_MCP_PROXY_PROFILES": "fcp"` on the `aws-mcp` server. Owner screenshots that config block (account id blurred) and Kiro calling an AWS MCP tool successfully.
  - 0.3c Kiro runs `aws sts get-caller-identity --profile fcp` and creates something visible: an S3 bucket `fcp-proof-<random>` in us-east-1 tagged `Project=full-court-press`. Save the transcript to `proof/transcript-0-3.txt` (account id redacted).
  - 0.3d After about 15 minutes, owner opens CloudTrail Event history for that session (filter by the identity `aws sts get-caller-identity` returned), screenshots the list, and exports 2 or 3 events (CreateBucket, PutBucketTagging) to `proof/cloudtrail-*.json` with account id redacted. The `userIdentity` and `userAgent` fields are the evidence: the user agent shows the CLI/MCP tooling made the calls, not a human clicking in the console.
  - 0.3e Owner screenshots the console showing the bucket exists and its Project tag.
  - Keep everything under `proof/`. LEDGER entry records what was captured, with timestamps matching CloudTrail. Do not paste the account id anywhere.
  - Note: AWS has not defined what "connected to the AWS console" means, and the FAQ post did not answer it as of Sep 20. Owner asks in the Discussion tab; if AWS names a specific mechanism, this task changes before Block 1.
  - _Requirements: contest_
- [ ] 0.3b Billing tag
  - Every Block 0 cloud resource gets the tag `Project=full-court-press`, so the key appears in Billing early. Owner activates it under Cost allocation tags as soon as it appears (up to 24 hours).
- [ ] 0.4 Spike: BALLDONTLIE from Lambda, and which endpoints our tier allows
  - Owner puts the API key in SSM first (`/full-court-press/bdl-api-key`, SecureString). Kiro never sees the key value.
  - `spike/bdl_from_lambda.py`: one flat handler that reads the key from SSM and calls, in order: `/wnba/v1/games?dates[]=<a recent date>`, `/wnba/v1/player_stats?game_ids[]=<id from the first call>`, `/wnba/v1/standings`, `/wnba/v1/plays?game_id=<id>`. Return status code and byte size per call. Never print the key.
  - Question A: does the API answer from an AWS Lambda IP? yes/no
  - Question B: which of the four endpoints return 200 on the current tier? Player stats are required for the spotlight, box score and The Number. If they 401, the owner decides: upgrade to ALL-STAR ($9.99/mo) or cut those sections.
- [ ] 0.5 Spike: Bedrock model
  - `aws bedrock list-foundation-models` filtered to the candidate model; record lifecycle status and the exact model or inference profile id. One `converse` call with "reply with OK".
  - Question: is the model ACTIVE and callable in the owner's region? yes/no
- [ ] 0.6 Spike: Pillow in Lambda
  - `spike/card_in_lambda.py`: render a 1200x630 PNG with one line of text in Alfa Slab One, return byte size.
  - Question: does Pillow + a bundled TTF run in Lambda? yes/no
- [ ] 0.7 Spike: Polly neural
  - `aws polly describe-voices --engine neural --language-code en-US` in the chosen region; record which voices are available. One `synthesize-speech` call with a 25-word test line, record the MP3 duration.
  - Question: does Polly neural work in the same region as Bedrock, and is a 25-word line about 10 seconds? yes/no
- [ ] 0.8 CHECKPOINT 0
  - PASS when 0.3 to 0.7 each have a recorded answer in LEDGER.md (0.2 already recorded), every task in this block has a BUILD-LOG.md entry, and all spike **cloud resources** are deleted
  - **Spike code is kept, not deleted.** `spike/` stays committed as a repo artifact: the throwaway
    scripts, `spike/THROWAWAY`, and whatever raw output was captured. "Discard" in the rigor tiers means
    not promoted into the product, never removed from the repo. Nothing in `spike/` is imported by
    product code, and the checkpoint still asks whether anything from `spike/` is in use.
  - Delete the cloud resources only: the proof bucket, `fcp-spike-bdl`, its role, and any log groups.
    List what was deleted in BUILD-LOG.md. Cloud resources cost money and widen the blast radius; files
    in git do neither.
  - Any "no": stop. Owner updates PRD.md and this spec before Block 1
  - _Requirements: 2, 5, 8_

## Block 1: Static UI from mock data (Tier: Working. Disposition: promote)
Tier: Working. Happy path + known edges only. No backend, no AWS calls.

- [ ] 1.0 Team colors
  - `design/team-colors.md` is the source for the spot color table. Lift it verbatim into the product.
  - Three teams (GS, POR, TOR) are marked UNVERIFIED. Until the owner confirms them, those teams fall
    back to `--spot`. Do not invent a value and do not fetch one from an unofficial source.
- [ ] 1.1 Extract the design from the approved mockup
  - `design/full-court-press-mockup.html` is the design source of truth. Lift the CSS custom properties, type scale, spacing, component styles, print rules and section order from it into `static/styles.css` and `static/print.css`. Self-host the two fonts from `static/fonts/`.
  - Do NOT redesign, do not add colors or fonts, do not use `design/reference.html` (superseded).
  - The mockup is one issue page. The index ("All") page is described in requirements 10.1 to 10.1c and reuses the same components.
- [ ] 1.2 Mock facts
  - `fixtures/mock/` with 3 hand-written facts sheets (one normal, one OT, one where voices were dropped) matching the design.md schema
- [ ] 1.3 Templates
  - `_base.html`, `issue.html` (per the mockup), `today.html` (index of last night's slate, game cards, no recap text), `team.html`, `archive.html`, footer disclaimer, `og:image` tag pointing at that edition's card
  - `static/print.css`, `static/app.js` (team picker, voice switcher, try/catch on every fetch, `textContent` only)
- [ ] 1.3b About page
  - `templates/about.html` and a footer link on every page. Static copy, no data, no JS.
  - Content per Requirement 10c. Owner writes the byline line and the "what this is" paragraph; leave
    `<!-- OWNER -->` markers where her words go and do not invent them.
  - No payment link, no donation link, no third-party embed, no tracking.
  - Footer partial, used by every template: "Data from BALLDONTLIE" with BALLDONTLIE linked to
    https://www.balldontlie.io, rel="noopener", plus the About link. Server-rendered, no JS.
- [ ] 1.4 Local render
  - `render.py` + a dev script that renders mock fixtures to `./out/`
- [ ] 1.5 CHECKPOINT 1
  - `./out/` issue pages open locally, match the reference look, print to one page, work at 375px wide, empty state shows when JSON is missing, reduced-motion stops the ticker
  - _Requirements: 7, 9, 10_

## Block 2: Facts from real data (Tier: Working. Disposition: promote)
- [ ] 2.1 `league_config.py` with NBA STUB entry
- [ ] 2.2 `bdl_client.py` + `secrets.py` per design (auth header, spacing, per-run cap, 429 backoff, 401 handling, timeout, key never logged)
- [ ] 2.3 Golden set: fetch and save 5 WNBA 2026 games (game + player_stats each) to `fixtures/golden/` (include an OT game if one exists; owner approves the list). Also commit `team_colors.json` for the 15 teams.
- [ ] 2.4 `facts.py` (games + player_stats -> facts sheet, quarters included), `game_of_night.py` + `gotn_rules.json`. `runs.py` is a STUB comment only unless Block 0 showed the plays endpoint is available.
- [ ] 2.5 Tests for facts, quarters, game_of_night (design.md Testing)
- [ ] 2.6 Render golden games with a mock voice to `./out/`
- [ ] 2.6b Derived statistics from play-by-play (Requirement 3b)
  - `zine/pbp_stats.py` per design.md. Points, FGM, FTM, rebounds, assists, steals, blocks, turnovers.
    Exact roster name matching, no fuzzy matching. No minutes, plus-minus, percentages or attempts.
  - First, print the distinct `type` values across the 5 golden games before writing the classifier.
    Do not guess the vocabulary. Report the list.
  - The reconciliation gate is the acceptance test: for each of the 5 golden games, derived player points
    per team must equal that team's final score. Report the pass rate across the golden set.
  - If a game fails, `scoring_lines` is absent and the dependent sections are omitted. Verify that path
    with a deliberately broken fixture, not only with the happy path.
  - Report how many of the 5 golden games reconciled. **Owner cut rule: fewer than 4 of 5 reconcile and
    derived scoring is dropped entirely, back to runs and standings.** Do not tune the matcher to hit
    the number; report what it does.
- [ ] 2.6c Runs and standings (promoted from STUB)
  - `zine/runs.py` per design.md. A run never crosses a period boundary.
  - Standings line per team from `/wnba/v1/standings`: wins, losses, playoff seed. Nothing else.
- [ ] 2.7 CHECKPOINT 2
  - Facts for all 5 golden games match their raw JSON (Kiro compares scores, leaders and one player line per team against the raw file and shows the comparison)
  - Tests pass. No odds, props or injury data anywhere in the output (grep). The API key appears in no log, no fixture and no task summary (grep)
  - _Requirements: 2, 3, 4, 11, 13_

## Block 3: Voices and fact lock (Tier: Working. Disposition: promote)
- [ ] 3.1 `voices.py` (two MUST voices, two STUB comments), `output_schema.py`
- [ ] 3.2 `voice_client.py` (Converse, `MODEL_ID` env, no prompt/response logging)
- [ ] 3.3 `fact_lock.py` + retry-once-then-drop flow
- [ ] 3.4 Tests for fact_lock and output_schema (design.md Testing)
- [ ] 3.5 Run golden set x 2 editions x 2 voices locally against Bedrock, render to `./out/`
- [ ] 3.6 CHECKPOINT 3
  - 20 voice results (5 games x 2 editions x 2 voices): every rendered section passed the lock; losing editions follow the tone rule (owner reads 2); dropped sections show the "writers' room passed" state
  - Planted wrong number is rejected (test and one live call with a doctored facts sheet)
  - Owner reads 2 issues and approves the voices (owner decides, Kiro doesn't grade tone)
  - _Requirements: 5, 6_

## Block 4: Share card (Tier: Working. Disposition: promote)
- [ ] 4.1 Bundle Alfa Slab One + Archivo TTFs and OFL licenses in `static/fonts/`
- [ ] 4.2 `card.py` per design.md share card spec, text fitting rules (shrink to a floor, then ellipsis), one card per edition, contrast pick for text on the team color. Reference output: `design/card-*.png`
- [ ] 4.3 CHECKPOINT 4
  - Cards for all golden games x both editions: nothing overflows, only locked or deterministic text, no logos or photos, pale team colors still readable
  - _Requirements: 8_

## Block 5: Ship it (Tier: Full. Disposition: promote)
Full tier: the 11-point checklist applies to everything this block touches.
- [ ] 5.1 `template.yaml`: bucket (private, versioning), CloudFront + OAC + headers policy, hunter Lambda (timeout, env vars, least-privilege role incl. `ssm:GetParameter` on the one key parameter and `kms:Decrypt`), EventBridge Scheduler (morning, America/Los_Angeles), Budgets budget $10/month filtered to `Project=full-court-press` + Polly (alerts 50%/100% actual, 100% forecast), Bedrock application inference profile `fcp-recap` tagged and used as `MODEL_ID`, `Project` tag on every resource
- [ ] 5.2 `cache.py`, `publish.py`, `state.py`, `league_strip.py`, `hunter.py` (handler only orchestrates)
- [ ] 5.3 Publish golden set to `site/golden/`
- [ ] 5.4 `sam deploy` (owner approves before running)
- [ ] 5.5 CHECKPOINT 5 (proven on the deployed stack)
  - A scheduled run, with nobody touching it, publishes last night's games to the public URL
  - Direct S3 URL returns access denied
  - Live response headers include the full policy
  - CloudWatch after the run shows game ids and lock results only (no prompts, no model text, no account ids)
  - Run log shows request spacing, the per-run cap and no API key
  - Budgets alarm exists in OK state
  - Cost Explorer grouped by the `Project` tag shows spend for `full-court-press` (once the tag is active)
  - _Requirements: 1, 9, 10, 11, 12_

## Block 5b: Audio recap (Tier: Full, it touches the live stack. Disposition: promote)
Cut rule: if CHECKPOINT 5 is not passed by end of day Sep 29, skip this block and mark Req 16 STUB. The site ships without audio.
- [ ] 5b.1 `audio_script.py` + test (script under 30 words, digits only from facts, overtime phrase only when OT)
- [ ] 5b.2 `audio_client.py` (neural only, try/except, no text in logs)
- [ ] 5b.3 Add `polly:SynthesizeSpeech` to the Lambda role in `template.yaml` (nothing broader), plus `POLLY_VOICE`, `POLLY_ENGINE`, `MAX_AUDIO_PER_RUN`
- [ ] 5b.4 Player + visible transcript in `issue.html`, `preload="none"`, no autoplay
- [ ] 5b.5 CHECKPOINT 5b
  - Deployed run produced MP3s for last night's games and the golden set; owner listens to 2 and approves the voice
  - Transcript on the live page matches the script exactly
  - CloudWatch shows no script text
  - _Requirements: 16_

## Block 6: Harden and package (Tier: Full. Disposition: promote)
- [ ] 6.1 Walk the 11-point checklist (PRD Gate H), record each item PASS / N/A / deferred with reason
- [ ] 6.2 Planted-bad-number test against the deployed Lambda (doctored facts, invoked once), rejection visible in CloudWatch
- [ ] 6.3 Judge view: live site on a phone size and a laptop size, cold browser, golden link works, print works
- [ ] 6.4 README: what it is, how it's made, limitations (unofficial data feed, two voices, WNBA only), STUB list and NBA reactivation condition, data credit with the BALLDONTLIE link, sign-off
  - Include a section titled "The spikes" covering `spike/`: what each throwaway script asked, what it
    answered, and that none of it is used by the product. Link the matching LEDGER.md entries. The point
    is that a reader can see the questions that got asked before any product code existed.
- [ ] 6.5 CHECKPOINT 6
  - Everything in 6.1 to 6.4 recorded with evidence
  - _Requirements: 12, 15_

## Block 7: Wind down (owner, after judging)
- [ ] 7.1 After the WNBA Finals: disable the schedule, leave site up through judging
- [ ] 7.2 If spend passes the Budgets threshold: disable the schedule
- [ ] 7.3 Final LEDGER.md entry, whatever the result
- _Requirements: 15_
