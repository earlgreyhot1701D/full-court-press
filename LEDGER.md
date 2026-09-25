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

### 2026-09-23 . Block 0 . 0.4 BALLDONTLIE from Lambda
Question A: Does the API answer from an AWS Lambda IP? YES. /wnba/v1/games?dates[]=2026-09-22 returned 200, 1408 bytes, 3 games (game_id 25072).
Question B: Which of the four endpoints return 200 on the current (free) tier? Only games (200). player_stats 401, standings 401, plays 401 (each 12-byte body).
Evidence:     Throwaway Lambda fcp-spike-bdl (python3.13, us-east-1, tag Project=full-court-press) reads the key from SSM at runtime, never prints it; invoked once, StatusCode 200. Response saved to spike/bdl_out.json. Key value never seen by Kiro.
Implication:  player_stats is required for the player spotlight, box score and The Number. 401 means the current tier does not include it. This is the owner's spend decision: ALL-STAR $9.99/mo per sport, or cut those three sections. standings (Around the League) and plays (scoring runs) are GOAT-tier and were already STUB per tech.md; their 401 confirms that.
Cost:         ~15 min. Lambda fcp-spike-bdl + role fcp-spike-bdl-role to be deleted at 0.8.
Disposition:  STOPPED for owner decision (mandated stop: player stats 401).
Changes PRD?: pending owner decision.

### 2026-09-23 . Block 0 . Identity: staying on root
Question:     Switch the agent's AWS profile off the account root identity before deploy?
Answer:       No. Owner decision, this project only.
Known cost:   Least privilege not satisfied. CloudTrail shows `root`, which is weaker proof than a scoped identity.
Compensating: Agent creates no credentials. One SSM SecureString. Everything tagged. $10/$25 spend limits. Deploy approved by hand.
Disposition:  promote (tech.md "Identity")
Changes PRD?: yes. The authorization line in the 11-point checklist mapping is a documented exception, not a pass.

### 2026-09-23 . Block 0 . Data tier: upgrading to ALL-STAR
Question:     player_stats returned 401 on the free tier (see BUILD-LOG 0.4). Pay $9.99/mo for ALL-STAR, or cut the spotlight, box score and The Number?
Answer:       Pay. ALL-STAR, $9.99/month, WNBA only.
Cost:         $9.99/month, inside the $25/month wind-down ceiling. Cancelled at wind down.
Why:          Player stats feed three issue sections. Without them the issue is final scores and quarter scores, which is thin for a zine.
Disposition:  promote. Re-run the 0.4 spike Lambda after the upgrade to confirm player_stats returns 200.
Changes PRD?: yes. Data cost line, and the spotlight/box score/The Number sections stay MUST.

### 2026-09-23 . Block 1 . About page added, support link deferred
Question:     Add an About page, and put a "buy me a coffee" link on it?
Answer:       About page yes, MUST, new Requirement 10c. Support link no, STUB until after judging.
Why:          The About page is where provenance, the fact lock, the no-affiliation statement and the honest limitations live. It is also the page a judge reads to decide whether to trust the numbers.
              The tip link is deferred for three reasons: the zine's own pitch leads with "non-commercial", so a tip jar undercuts the story being told to judges; BALLDONTLIE's terms bar reselling data and competing with them, and a revenue line on a data-derived site is a gray area not worth entering during judging; and a third-party widget adds a script and an embed to a page that must stay readable with JavaScript off for the AI scorer.
Disposition:  promote (Requirement 10c, task 1.3b, Requirement 14 STUB list)
Changes PRD?: yes. New MUST, and one line in the STUB list.

### 2026-09-23 . Block 1 . Attribution guardrail for BALLDONTLIE
Question:     BALLDONTLIE's terms say no attribution is required. Credit them anyway?
Answer:       Yes. Owner decision. Every page footer carries "Data from BALLDONTLIE" linked to https://www.balldontlie.io, and the About page credits them in a sentence.
Why:          Practice, not obligation. A zine that claims its numbers can be checked should say where they came from. It also makes the provenance visible to a judge in one glance.
Limits:       A credit is not an endorsement. The About page states non-affiliation with BALLDONTLIE, the WNBA and every team. Raw feed data is never republished as a dataset or an API.
Disposition:  promote (guardrails.md "Attribution", Requirement 10c, task 1.3b)
Changes PRD?: yes. One line in the guardrails mapping.

### 2026-09-23 . Block 0 . 0.5 Bedrock model
Question:     Is Claude Haiku 4.5 ACTIVE and callable in us-east-1? yes/no
Answer:       YES. Base model anthropic.claude-haiku-4-5-20251001-v1:0, lifecycleStatus ACTIVE, but inferenceTypesSupported is INFERENCE_PROFILE only (no ON_DEMAND), so Converse must target an inference profile, not the bare model id. Two ACTIVE system-defined profiles exist: us.anthropic.claude-haiku-4-5-20251001-v1:0 and global.anthropic.claude-haiku-4-5-20251001-v1:0. One Converse call via the us. profile returned "OK". No console model-access enablement was needed.
Cost:         ~5 min, 1 attempt. No resource created.
Disposition:  Confirms tech.md plan: MODEL_ID will be the fcp-recap application inference profile ARN (not created yet, awaiting owner). The us. system profile can seed it.
Changes PRD?: no.

### 2026-09-23 . Block 0 . 0.6 Pillow in Lambda
Question:     Does Pillow plus a bundled TTF run in Lambda? yes/no
Answer:       YES. Pillow 12.2.0 (manylinux2014_x86_64/cp313) loaded a bundled TTF and rendered a 1200x630 PNG (13076 bytes) in a python3.13 Lambda.
Note/FAIL:    The Alfa Slab One TTF the task expected in design/ is NOT present in the repo (design/ has only PNGs, HTML and PDFs). Spike used the upstream OFL Alfa Slab One from Google Fonts for the mechanism test. Owner action for Block 4/task 4.1: add the real TTFs (+ OFL license) to static/fonts/. This is a spec-vs-reality gap: tasks.md 0.6 says "the TTF is in design/".
Cost:         ~15 min, 2 attempts (create raced with a status check; second confirmed it existed).
Disposition:  bundling approach works; font asset gap flagged for Block 4.
Changes PRD?: no, but the missing design/ TTF should be reconciled before Block 4.

### 2026-09-23 . Block 0 . 0.7 Polly neural
Question:     Does Polly neural work in the same region as Bedrock, and is a ~25-word line about 10 seconds? yes/no
Answer:       YES to region. 13 neural en-US voices in us-east-1 incl. Danielle and Ruth (both list "neural"). Timing: a 23-word line measured 6.79s (MP3 frame count; speech-mark last word start 6.06s). So ~25 words is ~7s and a ~30-word script reaches ~9-10s. The audio_script target should aim near 30 words to hit ~10s, still under the 30-word cap in tasks.md 5b.1. Neural engine only; generative on the NEVER list and not used. (Tiffany not in neural en-US, consistent with tech.md ruling her out.)
Cost:         ~10 min, 1 attempt.
Disposition:  Confirms POLLY_VOICE candidates Danielle/Ruth and neural default. Minor note for 5b.1: script length ~30 words (not 25) to hit ~10s.
Changes PRD?: no.

### 2026-09-23 . Block 0 . Spike code is kept, not deleted
Question:     At CHECKPOINT 0, "discard" the spikes. Does that mean deleting them from the repo?
Answer:       No. Owner decision. `spike/` stays committed as a repo artifact. Discard means not promoted into the product.
Why:          The spikes are the evidence that the questions got asked before any product code existed. That is the part worth showing. The README gets a "The spikes" section describing what each one asked and answered.
Still deleted: Cloud resources. The proof bucket, the throwaway Lambdas, their roles and log groups all go at the checkpoint. Files cost nothing; running infrastructure costs money and widens the blast radius.
Unchanged:    Product code never imports from `spike/`. Every checkpoint still asks whether anything in `spike/` is in use, and a yes stops the block.
Disposition:  promote (guardrails.md "What discard means", tasks 0.8 and 6.4)
Changes PRD?: yes. The rigor tier disposition wording.

### 2026-09-23 . Block 0 . 0.8 CHECKPOINT 0
Question:     Are all Block 0 spikes answered, all spike resources deleted, and is anything from spike/ still in use?
Answer:       PASS with one deferred teardown. All questions answered: 0.1 PASS, 0.3 PASS on three layers (two deferred), 0.4 (Q-A yes, Q-B only games; player_stats 401 -> owner chose ALL-STAR upgrade), 0.5 yes (Haiku 4.5 ACTIVE, inference-profile only), 0.6 yes (Pillow + bundled TTF; design/ TTF gap flagged), 0.7 yes (Polly neural, Danielle+Ruth, ~23 words 6.79s). Nothing from spike/ is imported by any source (only LEDGER.md/PRD.md mention it as docs). spike/ folder and branch spike/hook-check deleted.
Conflict:     Task 0.8 says delete fcp-spike-bdl, but the owner asked to re-run that Lambda after the ALL-STAR upgrade to confirm player_stats=200. Resolved by holding fcp-spike-bdl + role + log group; deleting bucket fcp-proof-7y2983ri, Lambda fcp-spike-card + its log group now. Held resources to be deleted immediately after the re-run.
Cost:         ~5 min. Verified against live state (HeadBucket 404, GetFunctionConfiguration ResourceNotFound, tagging API).
Disposition:  Block 0 complete pending the single held re-run. CloudTrail 0.3d/0.3e deferred.
Changes PRD?: no.

### 2026-09-23 . Block 0 . CHECKPOINT 0 passed with spike code partially reconstructed after the fact
Question:     After 0.8 deleted the uncommitted spike/ folder, could the spike code be recovered, and what was lost?
Answer:       CHECKPOINT 0 stands as PASS, but the spike code had to be recovered after the checkpoint because it was never committed before deletion (root cause: spike files were only committed at the checkpoint, not per task; see new guardrail "What discard means"). Recovered: spike/THROWAWAY (from dangling commit ac908b1); spike/bdl_from_lambda.py (from the deployed fcp-spike-bdl code, authoritative); spike/card_in_lambda.py and spike/mp3_duration.py (verbatim from session context, not reconstructed from memory of behavior); spike/bdl_out.json and spike/card_out.json (exact invocation outputs from session context). Committed b46bb9c as a kept artifact, not product code.
Lost (not reconstructed): spike/trust.json and spike/ssm-kms.json (the throwaway IAM policy docs for fcp-spike-bdl-role; regenerable); the Pillow build dir and card_build_pkg.zip (build artifacts); the downloaded OFL AlfaSlabOne-Regular.ttf (re-downloadable); polly_ruth.mp3, polly_line.txt, polly_meta.txt (Polly derived outputs; the numeric findings 6.79s/40796 bytes/132 chars survive in LEDGER and BUILD-LOG).
Cost:         ~10 min recovery. No cloud resource involved (fcp-spike-bdl still deployed, held).
Disposition:  spike/ committed on master. Process fixed by the new guardrail.
Changes PRD?: no.

### 2026-09-24 . Block 0 . player_stats 401 diagnosis (route vs tier)
Question:     Is player_stats 401 caused by a wrong WNBA path or by a tier/entitlement denial?
Answer:       TIER/ENTITLEMENT denial, not a wrong path. Probe against game 25072 on the held fcp-spike-bdl:
              games 200 (1408B); player_stats 401 body exactly "Unauthorized" (12B); stats 404 (27B); box_scores 404 (27B); box_scores/live 404 (27B); players?team_ids[]=5 200 (8092B).
              The 404s (27-byte body) are unknown routes: stats/box_scores/box_scores/live do NOT exist for WNBA. player_stats returns 401, not 404, so the route DOES exist and is recognized; it is refused for this key. So player_stats is the correct WNBA path and the block is authorization, not a bad URL.
              Contradiction to resolve on the provider side: this key gets 200 on GOAT-tier standings and plays but 401 on ALL-STAR-tier player_stats. That is not a tier ladder. Most likely a GOAT trial is active while the player_stats entitlement is not attached to this key, or the ALL-STAR line did not apply. AWS/SSM is not the cause: SSM parameter is still Version 1 (unchanged), so the key value never changed.
Cost:         ~15 min. Used the held fcp-spike-bdl (code updated to a routes probe, still tagged Project=full-court-press). No key change, no SSM change, nothing deleted.
Disposition:  Owner to check BALLDONTLIE plan/entitlements for the WNBA key (is player_stats included and active). Teardown of fcp-spike-bdl stays deferred until player_stats returns 200.
Changes PRD?: no yet. If player_stats cannot be enabled, the spotlight/box score/The Number decision from the ALL-STAR entry reopens.

### 2026-09-24 . Block 0 . WNBA endpoint tiers were inferred from NBA docs and were wrong
Question:     What does WNBA ALL-STAR actually grant, and where did our tier assumptions come from?
Answer:       We inferred the WNBA endpoint tiers from BALLDONTLIE's NBA documentation, because the NBA docs were the ones we found. tech.md explicitly said "confirm per sport in Block 0" and we did not. That cost a wrong STUB list (standings and plays were marked GOAT/STUB when they are actually ALL-STAR) and a wrong spend framing (we told the owner ALL-STAR would unlock player_stats; it does not).
Correct WNBA table (source: https://wnba.balldontlie.io, "Account Tiers"):
  - ALL-STAR ($9.99): standings, play-by-play (plays), active players, player injuries.
  - GOAT ($39.99): player_stats, team_stats, season stats endpoints.
Confirmed live on the owner's WNBA ALL-STAR key (paid Sep 23, renews Oct 23), probe against game 25072:
  standings 200 (77855B); plays 200 (137191B, 407 plays first page, next_cursor null); players/active 200 (7926B); player_injuries 200 (11758B). player_stats 401 "Unauthorized" is CORRECT for ALL-STAR (it is GOAT-only).
Note:         player_injuries is accessible on this tier but is on the guardrails NEVER-read list; it must not be read or published in the product. It was hit here once only for tier confirmation at owner request.
Cost:         The inference error burned the earlier player_stats spend decision and the runs/standings STUB calls. Diagnosis + confirmation ~30 min across two probes.
Disposition:  Owner is preparing a scope change. Do not edit the spec yet. fcp-spike-bdl still held (not deleted).
Changes PRD?: pending owner scope change (STUB list and which sections are buildable will shift: plays/standings now available, player_stats now the paid gap).

### 2026-09-23 . Block 2 . Scope change: count the points ourselves
Question:     WNBA player_stats is GOAT only ($39.99, above the $25 ceiling). Cut the player sections, derive them, or pay?
Answer:       Derive. Owner decision. Per-player POINTS are counted by code from the play-by-play, which is on our ALL-STAR tier. Nothing else is derived.
Scope:        Points, made field goals, made free throws. NEVER rebounds, assists, steals, blocks, turnovers, minutes, plus-minus, percentages or attempts: not reliably recoverable from play text, so they are absent rather than estimated. Double-doubles and triple-doubles become impossible to state and are never inferred.
Safety:       A reconciliation gate. Each team's derived player points must equal that team's final score from the games endpoint. Any mismatch or any unattributed scoring play drops every derived section for that game, and the issue publishes without them. Nothing derived is ever published unreconciled.
Labeling:     Every derived figure is labeled "counted from the play-by-play". The words "box score" never appear in the product. The About page explains the method and says full statistics sit behind a tier this project does not buy.
Cut rule:     Fewer than 4 of the 5 golden games reconcile at task 2.6b and derived scoring is dropped entirely, back to runs and standings. The matcher is not tuned to hit the number.
Also promoted: runs and standings move from STUB to MUST. Both are on ALL-STAR, which we only learned today.
Cost:         $9.99/month, inside the ceiling. One extra module, one extra roster call per game, and a real chance the cut rule fires.
Disposition:  promote (Requirement 3b, design.md pbp_stats.py, tech.md tier table, tasks 2.6b and 2.6c, Requirement 14 STUB list)
Changes PRD?: yes. Data tier, the issue section list, the STUB list, and a new deterministic module.

### 2026-09-23 . Block 1 . Team colors were wrong, all fifteen
Question:     Do the mockup's team spot colors match public record?
Answer:       No. Every one of the fifteen was wrong, from off-by-one-digit to wrong colour entirely.
Examples:     DAL, the mockup's default team, used #002b5c against an official navy of #0C2340. LA used #552583, which is the Lakers' purple, not the Sparks' #702F8A. LV used a silver that is neither the Aces' primary red #BA0C2F nor their actual silver. CON used an orange that is a secondary, not the primary red #A6192E. PHX used #3c286e against #201747. SEA was #2c5235 against #2C5234.
Fixed:        `design/team-colors.md` written with one sourced colour per team and the reason for each pick. The mockup's table and its default were patched to match. Three teams (Sky, Sparks, Storm) lead with a yellow that fails contrast on cream, so their second colour is used and the reason is recorded.
Unverified:   Golden State, Portland and Toronto are 2026 expansion clubs and are not on the source. Their values are the mockup's original guesses, marked UNVERIFIED, and they fall back to the pink until the owner confirms them from each club's own site. Task 1.0 enforces this.
Source:       teamcolorcodes.com, fetched Sep 23 2026.
Why it matters: nobody had checked. The colours came from memory and looked plausible, which is exactly why they survived several design reviews.
Disposition:  promote (design/team-colors.md, mockup patched, task 1.0)
Changes PRD?: no

### 2026-09-23 . Block 2 . Statistics scope widened, and a claim of mine corrected
Question:     Earlier the spec said rebounds, assists, steals and blocks were "not reliably recoverable from play text". Is that true?
Answer:       No, and the claim was mine, made without checking. The feed carries typed events (`Defensive Rebound`, block and steal text naming the player), so those categories are extractable.
Real distinction: points have an independent check, the final score from a different endpoint, so a miscount is caught by arithmetic. The other categories have none. Sanity checks catch impossible values (assists exceeding made field goals, steals exceeding opponent turnovers) but cannot catch a missing event. So points are verified; the rest are counted.
Decision:     Owner: the stat line stays, because stats are how fans argue and the landing page already shows one. Points keep the hard reconciliation gate. Each other category has its own gate and is dropped alone when it fails, rather than taking the game down with it. Minutes, plus-minus, percentages and attempts stay out: no denominator, no number.
Honesty:      The About page and the submission post state that points are verified against the final score and the other categories are counted but unverified, because nothing independent exists to check them against.
Disposition:  promote (Requirement 3b rewritten, design.md pbp_stats.py, task 2.6b)
Changes PRD?: yes. The issue section list and the limitations language.

### 2026-09-24 . Block 0 . Teardown complete
Question:     Are all Block 0 spike cloud resources now deleted?
Answer:       YES. Deleted fcp-spike-bdl (Lambda), fcp-spike-bdl-role (IAM role, after detaching AWSLambdaBasicExecutionRole and deleting the ssm-kms-read inline policy), and log group /aws/lambda/fcp-spike-bdl. Verified against live state: GetFunctionConfiguration ResourceNotFound, GetRole NoSuchEntity, DescribeLogGroups returns 0. Tagging API (Project=full-court-press) now returns only the SSM parameter /full-court-press/bdl-api-key, which is the permanent key, not a spike resource. The hold was released because the WNBA tier finding confirmed player_stats 401 is correct behavior, so no further re-run was needed.
Cost:         ~5 min.
Disposition:  Block 0 teardown done. spike/ code kept in git (commits b46bb9c, 3ff4a25, e811011). CloudTrail 0.3d/0.3e remain deferred.
Changes PRD?: no.

### 2026-09-23 . Block 1 . The index page had no design
Question:     Requirement 10 specifies the index ("All") page in prose. Is that enough to build from?
Answer:       No. Every other screen had a mockup that is the binding design source of truth; the index had only requirement text, so Kiro would have invented a layout at build time and the first time anyone saw it would have been CHECKPOINT 1.
Fixed:        `design/full-court-press-index-mockup.html` built and rendered: masthead, team picker, Around the League ticker, one card per game with both teams, scores, spot-colour swatches, status, Game of the Night badge, archive strip, footer credit. Task 1.1 now names both mockups as binding.
Found while building: a fan of the losing team had no way in. Tapping a card opened the winner's edition and they had to toggle. Both team names on a card are now direct links to that team's edition (Requirement 10.1b-i), server-rendered, working with JavaScript off.
Also added: 10.1b-ii pins down what a card shows and, more usefully, what it does not. No recap text, no stat line, no model output on the index.
Disposition:  promote (Requirement 10.1b, 10.1b-i, 10.1b-ii, task 1.1, new mockup)
Changes PRD?: no

### 2026-09-23 . Block 1 . Section order approved, runs placed, and no page is a dead end
Question:     Where do scoring runs go, and is the issue running order final?
Answer:       Owner approved the running order as mocked. Runs go inside the game flow panel, not a panel of their own.
Why inside:   A run never crosses a period boundary, which the spec already required, so every run belongs to exactly one quarter and nests inside that quarter's row. One panel answers "how did this game go" instead of two circling it. The print sheet has eight panels and no spare. A run that decided the game can still climb to The Number on the cover, so nothing is buried.
Found while clearing the banner: there was no way back to the index from anywhere on the site. Someone arriving from a shared link was stuck on that issue. New Requirement 10d: every page links home from the masthead, above the fold, server-rendered, working with JavaScript off, and hidden in print because a folded paper zine has no links.
Also fixed:   Requirement 7.1 said "box score", now "stat line". Requirement 9.2 was conditional on the tier including standings; the tier does, confirmed Sep 23, so it is now unconditional.
Disposition:  promote (Requirement 7.1, 7.1a-i, 7.1a-ii, 9.2, new 10d, issue mockup patched, OPEN banner cleared)
Changes PRD?: yes. The banner is gone and Block 1 is open.

### 2026-09-24 . Block 1 . Fonts self-hosted; Archivo as a variable font
Question:     How to satisfy "self-host Alfa Slab One and Archivo, all glyphs present" without the mockups' subset base64 faces?
Answer:       Downloaded both from the Google Fonts GitHub repo (OFL) into static/fonts/ with each family's OFL.txt so the licence travels with the files. Alfa Slab One ships as a single static TTF. Archivo in the repo is a variable font (Archivo[wdth,wght].ttf); saved as Archivo-VariableFont_wdth_wght.ttf and declared @font-face with font-weight:100 900, which covers the 400/600/800 weights the mockups use in one file. The mockups' embedded base64 faces were NOT used (they are subset to the sample copy and would miss glyphs the real content needs, per task 1.1). Verified: a stdlib cmap check (tests/test_font_glyph_coverage.py) shows all 43 distinct characters across the 15 team names and abbreviations resolve in both fonts.
Cost:         ~20 min. One extra API lookup to find the variable-font filename in the repo.
Disposition:  promote. Task 4.1 now only verifies the fonts and licences are present.
Changes PRD?: no.

### 2026-09-24 . Block 1 . Site footer is required by spec but not in the mockups
Question:     The mockups have no site-wide footer, yet Req 7.4/10c require a disclaimer and "Data from BALLDONTLIE" on every page. Build it or stop?
Answer:       Built a minimal site footer (_base.html) using only existing design tokens, no new palette or fonts: the guardrails disclaimer, the BALLDONTLIE attribution link (rel=noopener), and screen-only nav links. This is a spec requirement the mockups do not cover, not a redesign. Same reasoning for the small "writers' room passed" state, the run-inside-game-flow line, the edition-toggle link styling, and the About page blocks. jinja2 3.1.6 installed (named in tech.md, so in scope).
Cost:         ~30 min for all templates. No cloud resource.
Disposition:  promote (templates/, render.py, app.js, styles.css additions). requirements.txt still not created/pinned: Block 1 is Working tier and tech.md pins only when a Full-tier block says so.
Changes PRD?: no.

### 2026-09-23 . Block 2 . The OpenAPI spec existed and we were not using it
Question:     BALLDONTLIE publishes a machine-readable OpenAPI spec at https://www.balldontlie.io/openapi/wnba.yml. Were we using it?
Answer:       No. The endpoint list in tech.md was hand-written from the NBA documentation, which is the same shortcut that produced the wrong tier table. The spec is now named in tech.md as the authoritative contract: when it and tech.md disagree, the spec wins.
Finding 1, significant: **a play object has no player field.** Its fields are id, game_id, order, type, text, home_score, away_score, period, clock, scoring_play, score_value, team. design.md had said the scorer would be resolved "from the play's structured fields where present"; there are none. Attribution for every derived statistic is text-only, matched against the roster from the players endpoint. That raises the risk on Requirement 3b and makes the points reconciliation gate load-bearing rather than belt-and-braces.
Finding 2: the spec does not enumerate the values of `type`, so the category vocabulary still has to be discovered from real data. Task 2.6b already required printing the distinct values first, and that step is now mandatory rather than cautious.
Finding 3: `/wnba/v1/plays` takes `game_id` only, required, with no pagination. Consistent with the 407-play single response observed in the 0.4 spike.
Disposition:  promote (tech.md authoritative-source note, design.md pbp_stats.py attribution section)
Changes PRD?: no, but the derived-statistics risk is higher than when the scope change was approved.

### 2026-09-24 . Block 1 . Render-time contrast, and a silent dropped column was a broken promise
Question:     The design pass found the team colour text was invisible on most teams and a dropped stat category vanished silently. Fix in the renderer?
Answer:       Yes. Text colour on the spot colour is now decided at render time in src/zine/contrast.py (WCAG relative luminance and contrast ratio, pure Python, no dependency) and emitted as data-on-spot / data-lowc on <html>, never in JS, so the no-JS baseline reads correctly. All 15 teams clear 4.5:1 with the chosen colour; none needs the low-contrast escape hatch. The dropped-category note is a correctness fix, not polish: the About page promises the reader sees where a count was cut, and a silently missing column broke that promise. The stat line now carries one plain line, e.g. "Assists aren't shown for this game. The count didn't add up, so we left them out."
Note:         RENDER-CONTRAST.md lists default pink ink-on-pink at 4.3:1; the standard WCAG 2.x formula gives 5.6:1. The decision is identical (ink, and it passes), and contrast.py matches all five verified team figures in the doc exactly (DAL 13.7, NY 9.1, GS 6.8, LV 5.7, CHI 5.1). Kept the WCAG value; did not bend the math to the doc's number.
Cost:         ~40 min. No cloud resource. Owner's six CSS fixes left intact, re-rendered on top.
Disposition:  promote (contrast.py, test_contrast.py, template + style updates).
Changes PRD?: no.

### 2026-09-24 . Block 2 . Golden set chosen, and an overtime game that was there all along
Question:     Does an overtime game exist in the available data, for the golden set?
Answer:       Yes: game 25014, Indiana 95 at Atlanta 91, Aug 16 2026, game object `period: 5`.
What happened: Kiro's widened discovery scan found it and wrote it to `_golden_candidates.json` (62 games, 1 OT). Kiro then read that file back through a command whose stdout was swallowed or stale, saw "total 44, ot 0" from the earlier and smaller scan, and reported to the owner that no overtime game existed. The file on disk contradicted the report. Found by Claude reading the file directly.
Also settled: Kiro had concluded that the game object's `period` "won't reveal OT" because a regulation game showed 4. That was not evidence either way, and game 25014 disproves it: the game object shows period 5. Design: `overtime_periods = game.period - 4`, cross-checked against the max play period; if the two disagree, omit it and log both.
Golden set: 25014 (overtime), 25071 PHX/DAL (margin 1), 25057 POR/PHX (margin 3), 25066 TOR/NY (margin 37), 25064 GS/SEA (margin 13). Covers all three expansion teams, whose colours are still unverified. 25072 dropped to make room for the OT game.
Process:      The fetch runs on the owner's machine through `tools/fetch_golden.ps1`, not through an agent, to save Kiro credits; the key goes SSM to an environment variable for one process and is never printed or written. `tools/play_types.py` then builds PLAY_TYPES.md offline. Kiro's discovery scratch moved to `spike/golden-discovery/` under the discard rule.
Guardrails added: never print the caller identity unmasked (the first discovery command printed the full account id); read long-running results from a file, after the script finishes, never from stdout.
Disposition:  promote (tools/, design.md overtime_periods, guardrails.md two new rules)
Changes PRD?: no

### 2026-09-24 . Block 2 . 2.6b PASS: 5 of 5 golden games reconcile
Question:     Can per-player statistics be counted from the play-by-play accurately enough to publish? Cut rule: fewer than 4 of 5 golden games reconciling on points drops derived stats entirely.
Answer:       PASS, 5 of 5. Each team's derived points equal its final score exactly in all five games, including the overtime game 25014. Zero unattributed events in any category. No category dropped. Every assist, steal and block mentioned anywhere in the play text is credited exactly once (checked against a raw count of mentions).
Found while building:
  - The vocabulary: 69 play types across 2,104 plays. Rebounds and turnovers have types; assists, steals and blocks do not, they are embedded in other plays' text. The classifier would have been wrong if written from a guess.
  - The roster gap: the players endpoint returns current rosters. Jaylyn Sherrod assisted for Atlanta in 25014 and is on neither roster. 1 name in 748 credited events, zero points. Closed exactly, not fuzzily: a game's roster now includes the names in that game's substitution lines.
  - Team events: "Fever defensive team rebound" and "shot clock turnover" belong to a team, not a player, and do not count as unattributed.
  - A bug caught before commit: blocked shots never say "misses", so 8 to 11 misses per game were invisible to the blocks sanity check. It still passed, but against a smaller bound than intended. Fixed, with a test.
  - A weak test caught before commit: one of Claude's own tests ended in `or True` and could not fail. Rewritten.
Honest limit, unchanged: points are verified; the other categories are counted. The sanity checks catch impossible values, not missing ones.
Cost:         One fetch run by the owner (21 requests), no Kiro credits.
Disposition:  promote (src/zine/pbp_stats.py, tests/test_pbp_stats.py, 18 tests passing; design.md updated)
Changes PRD?: no. Requirement 3b holds as written.

### 2026-09-24 . Block 2 . 2.6c PASS, and three things the real feed does that the spec did not expect
Question:     Can runs, quarter scores and a standings line be built from the golden fetch?
Answer:       PASS. All five games: quarters add up to the final, overtime shows as a fifth period, runs are real stretches of unanswered points inside one period, and standings filter to 2026.
Found, 1: the games endpoint carries only the final score. design.md said quarters came from it. They come from the running score on the plays instead.
Found, 2, the serious one: the feed logs some events late. 19 records across 4 of 5 games sit out of sequence, some filed under an earlier period, each carrying the scoreboard of its own moment. Read in list order the score appears to drop and jump back. It produced a phantom 8-0 run lasting zero seconds (25057), and it made Portland's first quarter read 20-20 instead of 26-20 while every total still matched, so the add-up check passed on wrong numbers. DAL at PHX was wrong the same way and nobody had noticed. Fix: `zine.timeline` sorts plays into true game order (period, then clock counting down). In that order the score never drops, in any of the five games, which is the evidence the sort is right. Quarters also return None now if the score ever drops. These late records are real events, not duplicates, so the stat counter's totals were never affected.
Found, 3: the standings endpoint returns every season since 2008 unless asked for one (235 rows), and its `playoff_seed` is conference rank for every team, down to Seattle at 8-36. Printed as a seed it would tell a fan her team made the playoffs. Published as a place instead: "6th in the East". Mock fixtures reshaped to match; no template rendered it yet, so the change was cheap now.
Why it matters: the sum check was a real check and it was not enough. A check that proves totals cannot prove order.
Disposition:  promote (timeline.py, quarters.py, runs.py, league_strip.py; 12 new tests, 30 passing; design.md and tasks.md updated)
Changes PRD?: no

### 2026-09-24 . Block 2 . Facts sheet and Game of the Night on real games
Question:     Do the pieces assemble into one facts sheet per real game that the templates can render?
Answer:       Yes. All five golden games build with nothing missing, render at 390px with no errors, no "box score", no "seed", nothing from odds, props or injuries (tested). Game of the Night picks 25071 (one-point game, two 30-point scorers, a triple-double) over 25014 on the tie rule, later tip.
Found, 1: dates. A 7pm Pacific tip is 02:00 UTC the next day (25057), so the UTC date files West Coast night games under the wrong morning's issue. `date_local` is the US Eastern calendar day.
Found, 2: the provider has the two 2026 expansion teams with a blank city and a full name of just "Fire" and "Tempo", and the empty city had reached allowed_names. `league_config.TEAM_FILL` fills blanks only, never overrides, with sources.
Found, 3: The Number's caption had been guessed from the shape of a key name. The facts sheet now says what each number means (`number_labels`), built from facts only.
Decided: no mock voice on real games. Block 1's mock copy was invented sentences about invented numbers; the same thing on real games is invented sentences about real players. Voices render as "The writers' room passed on this one." until Block 3. The Spotlight panel is absent for the same reason: its text is the voice's. Its player and stat boxes are deterministic and could render without the voice; decide in Block 3.
Flag for the owner's CHECKPOINT 2 spot check: Alyssa Thomas's triple-double in 25071 (15 points, 11 rebounds, 12 assists) is the most headline-worthy claim the zine makes on counted, unverified categories. Check that line against Basketball Reference first.
Disposition:  promote (facts.py, game_of_night.py, gotn_rules.json, league_config.py, dev_render_golden.py; 43 tests)
Changes PRD?: no

### 2026-09-24 . Block 2 . 2.2 client, and a module renamed
Answer:       `bdl_client.py` enforces the rules from tech.md itself rather than trusting callers: bare-key auth header, one second spacing, per-run cap, 429 backoff with Retry-After, no retry on 401, 10 second timeout, and the NEVER-list endpoints (odds, props, injuries, player_stats) refused before any request is made. `api_key.py` reads the env var or SSM and never lets the key into an error message, tested with a deliberately leaky fake.
Deviation:    structure.md named the key reader `secrets.py`. That shadows Python's standard `secrets` module and can break unrelated imports in ways that are hard to trace. Renamed `api_key.py`; structure.md updated.
Checkpoint 2 criteria updated: there is no player_stats file to compare against, so the code-side evidence is the tested reconciliation, and the independent check is the owner's, by eye, starting with Alyssa Thomas's triple-double in 25071.
Disposition:  promote (54 tests passing)

### 2026-09-24 . Block 2 . CHECKPOINT 2 PASS
Question:     Do the counted stats hold up against an independent source?
Answer:       Yes. The owner checked by eye, in a browser, against Basketball Reference, and reported MATCH on every line checked: Alyssa Thomas in 25071 (15 points, 11 rebounds, 12 assists, the triple-double built on counted categories), the second 25071 line, and Allisha Gray in the overtime game 25014 (32 points, 7 rebounds, 5 assists). No Basketball Reference content was fetched, pasted, or given to any agent.
Code-side evidence: 5 of 5 golden games reconcile on points; quarters add up in true game order; overtime agrees between the game record and the plays; nothing from odds, props or injuries in any facts sheet; key-leak sweep clean; 54 tests passing.
What it means: rebounds and assists are still counted, not verified, on any given night. This check shows the counting method gets a real triple-double right, which is the evidence for letting counted categories carry a headline. The About page limitation stays as written.
Disposition:  Block 2 closed. Block 3 (voices and fact lock) is next.

### 2026-09-24 . Design . Zine energy layer (owner approved)
Question:     The pages read like a tidy dashboard. Can they feel like a fanzine without breaking contrast, print, or the fact rules?
Answer:       Yes. `static/zine-energy.css` adds a pink halftone behind the cover, masking tape on the score and The Number, a rubber-stamp FINAL, torn-paper fold edges, and handwritten margin notes. Owner reviewed a preview and approved.
Decided, 1: a third font, Caveat (OFL, license shipped beside it), for margin notes only.
Decided, 2: the fold line keeps its meaning. Owner asked that readers still know what it is for, so each fold carries a paper tab reading "fold here when you print".
Decided, 3: margin notes are fixed phrases shown only when a fact is true: "game of the night!" only on the picked game, "counted from every single play" only when player lines exist, "biggest run of the game" only on the first run of the largest size. The notes are aria-hidden decoration; the facts they point at are already in the page.
Found, 1: the halftone disappeared on dark team colors, so it is a fixed pink (#FF48B0), not the team color.
Found, 2: the draft note said "biggest run of the night", which is a claim about every game on the slate. It is only true of this game, so it now says "of the game" and sits on that run's row.
Found, 3: Caveat has no arrow glyphs, so the arrows would have fallen back to another font. Arrows are inline SVG, and a test checks every margin-note character exists in Caveat.
Found, 4: a tied quarter was labeled with the away team. It now reads TIED.
Disposition:  promote (55 tests passing; 25071 rendered at 390px, no horizontal scroll, no page errors)
Changes PRD?: no

### 2026-09-25 . Block 3 . 3.1 (schema) and 3.3 (fact lock), pure parts
Question:     Can a check with no model in it stop a voice from publishing a number or a name that is not in the facts sheet?
Answer:       Yes, for what it claims. `output_schema.py` rejects any response that is not exactly headline, recap, spotlight {player, text}, the_number_key, with the length limits; extra keys anywhere are invalid. `fact_lock.py` checks each section on its own: digits against `allowed_numbers`, spelled-out numbers, capitalized names against `allowed_names`, spotlight player, the_number_key. A planted 33 for Kahleah Copper's 31 fails the recap and leaves the headline standing.
Deviation, 1: design.md said names "not at sentence start" are checked. Read literally, "Diana Taurasi watched from the stands." would pass, because the name starts the sentence. Every capitalized word is now checked; the first word of a sentence is excused only if it is an ordinary word on a fixed list (`SENTENCE_STARTERS`). Tested.
Deviation, 2: single capitalized words are checked too, not only runs of 2+. A lone "Stewart" from another team would otherwise pass. Tested.
Deviation, 3: `spotlight.player` must be a full name from this game's stat line, not anything in `allowed_names`, which also holds team names and surnames. "Phoenix Mercury" as the spotlight player now fails.
Deviation, 4: "thousand" added to the spelled-number list.
Decided: a failure reason carries the offending token so the one retry can tell the model what to fix. The token is a piece of model output, so it never goes to a log: `log_safe()` strips it and is the only form that may be logged. `retry_note()` builds the retry message.
Found, 1: the golden-set name test caught a false reject on its first run: Te-Hina Paopao (25014). Hyphenated and apostrophe names now stay one word. Every player on all five golden stat lines passes by full name.
Found, 2: Title Case headlines fail ("Mercury Survive Wings In Thriller" reads as one long unknown name). The voice prompt must ask for sentence case. Documented in a test, not loosened.
Found, 3, for the owner: facts.py takes the last word of a name as the surname. For Li Yueru, "Li" is the family name, so the lock rejects "Li" and allows "Yueru". Nothing false gets published, but the allowed short form is the wrong one. Proposed fix: a small surname override in league_config, owner to approve.
What a pass does not prove (also in the module docstring): that a number is attached to the right claim ("Copper had 12 rebounds" passes if 12 is anywhere in the game, and 0 to 12 almost always are); that a spelled ordinal like "third quarter" is right; that we counted right.
Disposition:  promote (93 tests passing)
Changes PRD?: no

### 2026-09-25 . Block 3 . Family-name-first surnames (owner approved)
Answer:       `league_config.SURNAME` overrides the short form for players whose family name comes first in the feed: Li Yueru -> "Li" (25071), Han Xu -> "Han" (25066). Found on the golden set, not guessed. The full name is always allowed; only the short form changes. Rule: add a player only when the order is confirmed.
Disposition:  promote (95 tests passing)
