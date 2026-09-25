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

## 2026-09-24 . 0.8 . Teardown complete
- Tier: Spike
- Did: released the hold on fcp-spike-bdl (player_stats 401 confirmed correct for WNBA ALL-STAR) and deleted it, its role fcp-spike-bdl-role, and its log group. Verified deletions and ran the tagging API.
- Result: all spike cloud resources gone. Only Project=full-court-press resource remaining is the SSM key parameter. Block 0 teardown complete.
- Resources: deleted Lambda fcp-spike-bdl, role fcp-spike-bdl-role, log group /aws/lambda/fcp-spike-bdl.
- Evidence: GetFunctionConfiguration ResourceNotFound; GetRole NoSuchEntity; DescribeLogGroups 0; tagging API returns only the SSM parameter.

## 2026-09-24 . 1.0 . Team colors
- Tier: Working
- Did: created static/team_colors.json from design/team-colors.md verbatim, 15 teams, one spot hex each. Expansion teams GS/POR/TOR filled with their values and flagged unverified; the --spot fallback is not used. No value invented or fetched.
- Result: PASS. Data file matches the source table.
- Resources: none.
- Evidence: static/team_colors.json.

## 2026-09-24 . 1.1 . Extract the design (both mockups) + self-hosted fonts
- Tier: Working
- Did: downloaded Alfa Slab One and Archivo (OFL) from the Google Fonts repo into static/fonts/ with each family's OFL.txt; lifted the issue and index mockups into static/styles.css (tokens, type, spacing, components, home link + back bar per Req 10d) and static/print.css (8-panel fold layout, verbatim from the issue mockup print block); wired @font-face to the self-hosted files. Did not extract the mockups' embedded base64 faces; did not use reference.html; did not carry the index mockup's sample slate.
- Result: PASS. Glyph-coverage check (tests/test_font_glyph_coverage.py) confirms all 43 distinct characters in every team name and abbreviation resolve in BOTH fonts, so nothing falls back to a system font. pytest: 2 passed.
- Resources: none.
- Evidence: static/fonts/ (AlfaSlabOne-Regular.ttf, Archivo-VariableFont_wdth_wght.ttf, AlfaSlabOne-OFL.txt, Archivo-OFL.txt), static/styles.css, static/print.css, tests/test_font_glyph_coverage.py, out/font-check.html (gitignored render).

## 2026-09-24 . 1.2 . Mock facts
- Tier: Working
- Did: wrote four hand-written facts fixtures in fixtures/mock/ matching the design.md schema: a normal game, an overtime game, a dropped-voice game, and a game where points reconcile but one category (assists) fails its gate so that column is omitted (not zeroed).
- Result: PASS. All four are valid JSON; the category-gate fixture omits the ast key from player_lines entirely.
- Resources: none.
- Evidence: fixtures/mock/{normal,overtime,dropped_voice,category_gate_fail}.json.

## 2026-09-24 . 1.3 / 1.3b . Templates and About
- Tier: Working
- Did: built _base, issue, today (index), team, archive and about templates plus static/app.js. Issue page follows the approved section order with runs inside game flow, the edition toggle as direct server-rendered links, the stat line omitting a dropped category's column, and the "writers' room passed" state. Index has no recap/stat/model output and its masthead does not self-link. About drops the four OWNER-COPY.md blocks in verbatim with the spec-driven method, non-affiliation and non-commercial text, and no payment/donation/embed.
- Result: PASS. Owner blocks render verbatim with no double-escaping; category column correctly absent; dropped-voice shows the line and no spotlight/byline.
- Resources: none.
- Evidence: templates/*.html, static/app.js, static/styles.css (footer/about/edition-toggle additions).

## 2026-09-24 . 1.4 . Local render
- Tier: Working
- Did: added src/zine/render.py (Jinja2, autoescape on) and a Block 1 dev render script that builds view models from the fixtures and writes 10 pages to ./out/ (8 issue editions, index, about). Checked the no-JS baseline, the home link on every page, the viewport meta, the print fold order, and CSS/font path resolution by inspecting the rendered HTML.
- Result: PASS on the machine-checkable items. Visual checks (375px no-scroll, cover within first screen, actual printed fold) need the owner's eyes in a browser.
- Resources: none. Installed jinja2 3.1.6 (an allowed dependency per tech.md).
- Evidence: out/ renders (gitignored), font glyph test still green (2 passed).

## 2026-09-24 . design-pass . Four render-time fixes on the Block 1 render
- Tier: Working
- Did: implemented the four renderer items from design/DESIGN-PASS-SEP23.md on top of the owner's six CSS fixes (not reverted). (1) src/zine/contrast.py picks paper vs ink text on each team's spot colour at render time by WCAG contrast, and _base.html emits data-on-spot / data-lowc on <html>; (2) tests/test_contrast.py walks all 15 teams; (3) human dates ("SATURDAY, SEP 19, 2026") in the mastheads and "Last night"; (4) run bars scaled against the largest run in the game with a visible minimum; plus the visible dropped-category note and stat-line naming alignment.
- Result: PASS. Re-rendered out/. DAL text=paper, NY text=ink, all 15 teams clear 4.5:1; dates human; run widths proportional (e.g. 67% vs 100%); the gate-fail editions now say "Assists aren't shown for this game...". Tests: 5 passed.
- Resources: none.
- Evidence: src/zine/contrast.py, tests/test_contrast.py, templates/{_base,issue,today}.html, static/styles.css (.droppednote appended), out/ renders (gitignored).

## 2026-09-24 . 1.4b . Design pass follow-through (done by Claude on disk, not Kiro)
- Tier: Working
- Did: tap targets raised to the WCAG 2.2 24px minimum (styles.css); Around the League heading renamed "The rest of the slate" so an issue page no longer carries two "Last night" h2s; stat line eyebrow shortened to "Counted from the play-by-play" so it no longer wraps mid-phrase at 390px; RENDER-CONTRAST.md default-pink figure corrected to 5.6:1; added .gitattributes (eol=lf) which cleared three line-ending-only phantom diffs; *.bak gitignored.
- Result: PASS. Re-rendered with the existing dev renderer, pytest 5 passed, and all five page types checked in a headless browser at 390px: zero tap targets under 24px, correct data-on-spot on each page, no horizontal scroll, no page errors.
- Resources: none (local only).
- Evidence: design/DESIGN-PASS-SEP23.md items 11 to 13.

## 2026-09-24 . backfill . Claude's earlier on-disk work, Sep 23 (logged late)
- Tier: Working (design and spec; no product code, no AWS)
- Note: these changes were made directly on disk by Claude during the Sep 23 session and were committed by Kiro inside its own commits, so until now the log did not say who did them. Logged here late rather than inserted above, to keep the log append-only.
- Did, design:
  - `design/full-court-press-index-mockup.html` built and rendered, so the index had a binding design before Block 1
  - `design/team-colors.md` written after all 15 mockup colours were found wrong against public record; mockup table and default patched; the three expansion colours added with a sourcing caveat
  - First design pass on the Block 1 render: six CSS fixes in `static/styles.css` (the `.gotn` selector collision, the footer selector collision, run-line layout, focus states, reduced motion, and the `--on-spot` hooks), plus `design/RENDER-CONTRAST.md` and `design/DESIGN-PASS-SEP23.md`
  - Issue mockup: home link and back bar (Requirement 10d); every "box score" removed; `reference.html` moved to `design/_superseded/`
  - `OWNER-COPY.md` drafted from the owner's own zine origin story, for her to edit
- Did, spec (each recorded as a decision in LEDGER.md): Requirement 3b (statistics from play-by-play and its gates), 10b-i and 10b-ii (index cards), 10c (About), 10d (getting back); guardrails Attribution, What discard means, Build log split, Who works on this repo; tech.md Identity, corrected WNBA tier table, OpenAPI spec as the authoritative contract; design.md `pbp_stats.py`
- Result: all of the above verified by rendering in a headless browser at 390px or by re-reading the committed files
- Resources: none
- Evidence: commits by Kiro on Sep 23 and 24 that carried these files; LEDGER.md entries of the same dates

## 2026-09-24 . 2.0 . Golden set prep (Claude, on disk)
- Tier: Working
- Did: wrote `tools/fetch_golden.py` (stdlib only, about 25 requests, one second apart, raw JSON to `fixtures/golden/<id>/`, report to `FETCH-REPORT.txt`, key never printed or written) and `tools/fetch_golden.ps1` (SSM to env var for one process, removed afterwards); wrote `tools/play_types.py` (offline vocabulary report); found the overtime game Kiro's scan had recorded but misreported; moved Kiro's discovery scratch into `spike/golden-discovery/`; design.md and guardrails.md updated.
- Result: scripts parse; fetch not yet run. Owner runs it next.
- Resources: none.
- Evidence: LEDGER entry of the same date.

## 2026-09-24 . 2.6b . Statistics from play-by-play (Claude, on disk)
- Tier: Working
- Did: owner ran `tools/fetch_golden.ps1` (21 requests, all 200); generated `fixtures/golden/PLAY_TYPES.md` (69 types, 2,104 plays); wrote `src/zine/pbp_stats.py` against that vocabulary; wrote `tests/test_pbp_stats.py` covering the golden set and seven failure paths.
- Result: PASS. 5 of 5 golden games reconcile on points, zero unattributed events, every embedded assist, steal and block credited exactly once, overtime from the plays agrees with the game object. pytest 18 passed.
- Resources: none (BALLDONTLIE calls were the owner's, from her machine).
- Evidence: LEDGER entry of the same date; fixtures/golden/FETCH-REPORT.txt.

## 2026-09-24 . 2.6c . Runs, quarters, standings line (Claude, on disk)
- Tier: Working
- Did: wrote `src/zine/timeline.py`, `quarters.py`, `runs.py`, `league_strip.py`; reshaped `standings_line` in the four mock fixtures; `tests/test_runs_quarters_standings.py` with 12 tests.
- Result: PASS. Golden set: quarters add up and include overtime, zero score drops in true game order, no run crosses a period, standings filtered to 2026 and published as conference place. pytest 30 passed; dev render still builds every page.
- Resources: none.
- Evidence: LEDGER entry of the same date.

## 2026-09-24 . 2.1, 2.4, 2.5, 2.6 . Facts sheet, Game of the Night, golden render (Claude, on disk)
- Tier: Working
- Did: `src/zine/facts.py`, `game_of_night.py`, `gotn_rules.json`, `league_config.py` (NBA STUB, expansion-team name fill), `dev_render_golden.py`; `tests/test_facts_gotn.py`. Rendered the five golden games, both editions each, plus an index, to `out-golden/` (gitignored).
- Result: PASS. pytest 43 passed. All five pages render in a headless browser at 390px: no horizontal scroll, no page errors, correct contrast attribute, voices shown as passed (deliberately), no "box score" or "seed" text.
- Resources: none.
- Evidence: LEDGER entry of the same date.
