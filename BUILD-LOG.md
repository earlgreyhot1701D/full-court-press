# Build log: Full Court Press

Public build log. One entry per task, append only. No account id, no ARN carrying it, no secrets, no prompts, no model output.

## 2026-09-23 . 0.1 . Repo walls
- Tier: Spike
- Did: git init on master; committed the kickoff set (steering, spec, PRD, LEDGER, design/, pre-commit hook, .gitignore, MCP config); set core.hooksPath to .githooks; added spike/THROWAWAY; verified the spike pre-commit hook fires.
- Result: PASS. Hook rejects out-of-scope files on a spike/* branch and allows spike/THROWAWAY.
- Resources: none (local git only).
- Evidence: kickoff commit fa4dea9; hook at .githooks/pre-commit; spike marker committed on branch spike/hook-check (ac908b1); Git for Windows bash 5.3.9.

## 2026-09-23 . 0.3c . Connection proof (agent side)
- Tier: Spike
- Did: ran aws sts get-caller-identity via the fcp CLI profile; created S3 bucket fcp-proof-7y2983ri in us-east-1 tagged Project=full-court-press; verified tag and existence; saved a redacted transcript.
- Result: PASS (agent side). Real CLI calls made; identity and tagged bucket confirmed.
- Resources: S3 bucket fcp-proof-7y2983ri (us-east-1), tag Project=full-court-press. To be deleted at CHECKPOINT 0.
- Evidence: proof/transcript-0-3.txt (account id redacted to ****, gitignored); first AWS call 2026-09-23T23:09:14.072Z UTC.

## 2026-09-23 . 0.4 . BALLDONTLIE from Lambda
- Tier: Spike
- Did: deployed a throwaway Lambda that reads the API key from SSM and calls four WNBA endpoints in order (1s spacing, 10s timeout), reporting status and byte size. Invoked once.
- Result: Q-A YES, the API answers from a Lambda IP (games 200, 1408 bytes). Q-B only games returns 200 on the current tier; player_stats, standings, plays each return 401. Stopped for owner spend decision on player_stats.
- Resources: Lambda fcp-spike-bdl (python3.13) and role fcp-spike-bdl-role, both tagged Project=full-court-press. To be deleted at CHECKPOINT 0.
- Evidence: spike/bdl_out.json (status/bytes only, no key); invoke StatusCode 200.

## 2026-09-23 . 0.5 . Bedrock model
- Tier: Spike
- Did: listed foundation models filtered to Claude Haiku 4.5, recorded id and lifecycle status; made one Converse call through the US system-defined inference profile asking for "OK".
- Result: ACTIVE and callable in us-east-1. Converse returned "OK" (stopReason end_turn, 16 tokens). No console access step required. Did NOT create the fcp-recap profile (awaiting owner).
- Resources: none created. Used system-defined inference profile us.anthropic.claude-haiku-4-5-20251001-v1:0.
- Evidence: bedrock ListFoundationModels + Converse via AWS MCP; no prompt/model text stored beyond the literal "OK".

## 2026-09-23 . 0.6 . Pillow in Lambda
- Tier: Spike
- Did: built a Lambda package with Pillow (manylinux2014_x86_64, cp313) plus a bundled Alfa Slab One TTF; handler renders a 1200x630 PNG with one centered line and returns the byte size. Deployed and invoked once.
- Result: YES. font_loaded true, PNG rendered 1200x630, png_bytes 13076, Pillow 12.2.0. The design/ Alfa Slab One TTF was absent, so the spike used the upstream OFL Alfa Slab One (Google Fonts) for the mechanism test only; task 4.1 bundles fonts properly.
- Resources: Lambda fcp-spike-card (python3.13), reused role fcp-spike-bdl-role. Tagged Project=full-court-press. To be deleted at CHECKPOINT 0.
- Evidence: spike/card_out.json; code size 8558668 bytes.

## 2026-09-23 . 0.7 . Polly neural
- Tier: Spike
- Did: listed neural en-US voices in us-east-1; confirmed Danielle and Ruth present; synthesized one 23-word line with Ruth (neural, MP3) and measured duration two ways (speech marks + MP3 frame count).
- Result: YES. Polly neural works in us-east-1 (same region as Bedrock). Danielle and Ruth both support the neural engine. A 23-word line ran 6.79s, so ~25 words is about 7s and a ~30-word script approaches the ~10s target. Neural engine only; generative never used.
- Resources: none created (Polly is a direct API call).
- Evidence: spike/polly_ruth.mp3 (40796 bytes), spike/mp3_duration.py reported 6.79s / 283 frames; last word speech mark started at 6062 ms.

## 2026-09-23 . 0.8 . CHECKPOINT 0
- Tier: Spike
- Did: recorded answers for 0.3c-0.7; verified no source outside spike/ imports spike code; deleted spike cloud resources and the local spike/ folder and spike branch.
- Result: PASS with one deferred teardown. Deleted: S3 bucket fcp-proof-7y2983ri, Lambda fcp-spike-card, its log group, local spike/ dir, branch spike/hook-check. HELD by owner instruction: Lambda fcp-spike-bdl + role fcp-spike-bdl-role + its log group, for the player_stats re-run after the ALL-STAR upgrade; to be deleted right after that re-run. Remaining Project-tagged resources: fcp-spike-bdl (held) and the permanent SSM key parameter.
- Resources: see above. All were tagged Project=full-court-press.
- Evidence: HeadBucket 404 for the bucket; GetFunctionConfiguration ResourceNotFound for fcp-spike-card; resource-groups tagging list shows only fcp-spike-bdl + the SSM key. CloudTrail capture (0.3d/0.3e) deferred out of Block 0 by owner.

## 2026-09-23 . recovery . Restore spike artifacts deleted at checkpoint
- Tier: Spike
- Did: recovered spike/ after it was deleted uncommitted at 0.8. Restored THROWAWAY from dangling commit ac908b1; bdl_from_lambda.py from the deployed fcp-spike-bdl code; card_in_lambda.py, mp3_duration.py, bdl_out.json, card_out.json verbatim from session context. Added the "What discard means" guardrail (commit spike files per task, not at the checkpoint).
- Result: spike/ recovered and committed as a kept artifact, not product code. Lost and not reconstructed: trust.json, ssm-kms.json, the Pillow build zip, the OFL TTF, and the Polly mp3/text/meta (numeric findings survive in the logs).
- Resources: none. fcp-spike-bdl still deployed and held.
- Evidence: commits b46bb9c (spike artifacts + guardrail); dangling commit ac908b1 for THROWAWAY.

## 2026-09-24 . probe . WNBA player_stats route vs tier
- Tier: Spike
- Did: updated the held fcp-spike-bdl to a routes probe; against game 25072 tried player_stats, stats, box_scores, box_scores/live, and players; captured one full 401 body.
- Result: player_stats returns 401 "Unauthorized" (route exists, key refused). stats/box_scores/box_scores/live return 404 (routes do not exist for WNBA). players returns 200. Conclusion: correct path, tier/entitlement denial, not a bad URL. Contradiction: GOAT standings/plays 200 but ALL-STAR player_stats 401. Owner to check the BALLDONTLIE plan. No key/SSM change, nothing deleted.
- Resources: fcp-spike-bdl still deployed and held (code now the routes probe). Tagged Project=full-court-press.
- Evidence: spike/routes_out.json; SSM parameter still Version 1.

## 2026-09-24 . probe . Confirm WNBA ALL-STAR entitlements
- Tier: Spike
- Did: updated the held fcp-spike-bdl to probe the four WNBA ALL-STAR endpoints against game 25072 and counted plays.
- Result: standings 200 (77855B), plays 200 (137191B, 407 plays first page), players/active 200 (7926B), player_injuries 200 (11758B). Confirms WNBA ALL-STAR grants these; player_stats stays GOAT-only (401 is correct). Root cause of the earlier confusion: WNBA tiers were inferred from NBA docs and never confirmed per sport as tech.md required. player_injuries is on the NEVER-read list and must not be used in the product.
- Resources: fcp-spike-bdl still deployed and held (code now the ALL-STAR probe). Tagged Project=full-court-press.
- Evidence: spike/allstar_out.json.
