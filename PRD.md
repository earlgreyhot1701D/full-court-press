# Full Court Press: PRD v0.3

**Owner:** Shara (director). **Builder:** Kiro. **Architecture/docs:** Claude.
**Status:** v0.3 draft (Sep 19: guardrails in Gate G; one-pager on screen + foldable print; Polly neural audio recap; xerox + pink palette). Nothing built. Block 0 spike is the next action.
**Target:** AWS Builder Center "Zero to Shipped" hackathon. Due **Oct 2 2026, 11:59 PM PT**.
**Name:** Full Court Press (decided Sep 19).

> Single document, gated sections. Each gate is approved before the next section drives any build prompt.

> **Decided Sep 19:** name **Full Court Press**; team color option **stays**; screen is a one-pager and print is the 8-panel fold (`design/full-court-press-mockup.html`, `design/full-court-press-print-sheet.pdf`); Polly **neural**; team editions **yes** (each team's fans get their side); data source **BALLDONTLIE** (ESPN ruled out by the compliance gate); budget **$10/month AWS alarm, $25/month wind-down ceiling**, plus up to $9.99/month for the data tier, tracked by the `Project=full-court-press` tag. **Still open:** Polly voice, the who-it's-for sentence, and a final OK on the sections as mocked. Block 0 can start now; Block 1 waits for the section OK.

---

## Gate A. Contest constraints (fixed, from the Rules tab, read Sep 19 2026)

| Requirement | What it means for us |
|---|---|
| Live on AWS, public URL, reachable at evaluation | Static site on S3 + CloudFront. Must still be up weeks of Oct 5 and Oct 12. |
| Coding agent connected to the AWS console, documented proof | Connect via the **Agent Toolkit for AWS** (AWS CLI v2 + AWS MCP server + agent skills, browser `aws login`, profile `fcp`, region us-east-1). Five-layer proof in Block 0 (toolkit sign-in and MCP config screenshots, agent terminal transcript, CloudTrail events, console screenshot of what it built). See design.md "Connection proof". AWS still has not defined the bar: the FAQ post had no detail as of Sep 20 and nobody has asked. Owner asks in the Discussion tab. |
| Original, not previously published | New repo, new app. Nothing reused from shipped Clew tools except patterns. |
| One category tag + one lane tag | `#personal-expression` + `#community` |
| Builder Center project post | Describes app, dev process, how the coding agent was used, AWS services, live link |
| One entry per person | This is the entry. Cassandra Clew stays with Google SF. |

Judging: 25% each. Technical innovation and originality, implementation quality, community/market impact, creativity and storytelling. AI scoring first, then humans on the top 100.

---

## Gate B. Idea triage (project-judgment, Part One)

| Gate | Answer | Result |
|---|---|---|
| 1. Real friction, who is it for | Fans who want a morning-after recap with personality, fast, for any team, not only the headline games. WNBA fans who want last night's game in their team's voice by morning. Second audience: the Zero to Shipped judges. Draft in product.md, **Shara to put it in her own words**. | Drafted, pending Shara's wording |
| 2. Trigger without her | Yes. A scheduled morning run finds last night's finals and publishes. | PASS |
| 3. Excitement | "I think it's ripe." | PASS |
| 4. Agent or prompt in costume | Intermediate state: archive, cached games, last-run marker. Contingent steps: which games are final decides what gets built. | PASS |
| 5. Abuse surface | Real athletes are the subject. Roasting people, not performance, is the easy harmful version. Betting content is in the data feed. Both go in NEVER on day one. | PASS with NEVERs |
| 6. Spike | Block 0, criteria below. | Next |

"Can't be done in an LLM chat" test: PASS. A chat can't wake up on its own, fetch real box scores from a licensed source, guarantee every number, keep the same layout and card every day, or keep an archive.

---

## Gate C. Scope

### MUST
- **WNBA** games, any team, fan picks their team
- **Hunter:** scheduled run that finds finished games since the last run and builds an issue per game
- **Facts sheet:** deterministic JSON per game built from the box score
- **Zine issue page per game:** fixed layout, printable one-pager (print CSS)
- **Two team editions per game** (decided Sep 19): each team's fans get the recap from their side. Deterministic sections identical in both. Losing-side tone rule applies.
- **Two voices** pre-generated per edition at hunt time (see Voices)
- **Fact lock:** every number and every player name in AI text is checked against the facts sheet before publish
- **Share card:** one PNG per issue, built from fact-locked text only
- **Around the League:** small strip, all last-night scores + standings movers, deterministic
- **Game of the Night:** picked by a deterministic interest score
- **Archive:** browse past issues by date and team
- **Golden set:** a fixed set of cached games so the demo works even if the live feed is down
- Static public site. Visitors never trigger a model call.
- **Screen:** one condensed page per issue. **Print:** the same content as an 8-panel foldable mini zine via the browser's print (no server PDF).
- **Data:** BALLDONTLIE (`/wnba/v1/games`, `/wnba/v1/player_stats`). Quarter-by-quarter game flow. Standings and scoring runs are STUBs (GOAT tier).
- **Audio recap (~10 s):** Amazon Polly neural, reading a template script built from locked facts. Cut rule: if CHECKPOINT 5 isn't passed by end of Sep 29, audio becomes a STUB.

### STUB (comment stub with implementation notes, not built)
- **NBA league:** disabled league config entry. Same BALLDONTLIE shapes, path swaps `wnba` to `nba`. Turn on late Oct 2026.
- Voices 3 and 4
- Email or RSS subscription per team
- Downloadable PDF (print CSS covers printing for now)
- Fantasy playoffs zine (separate idea doc)
- Server-built PDF per issue
- Full team palettes (beyond the team spot color)

### NEVER
- Real media personalities' names, voices, or catchphrases
- Team or league logos, player photos, league marks
- Commentary on players' bodies, personal lives, off-court matters, or injuries
- Betting, odds, spreads, picks (the feed includes `odds`, `pickcenter`, `againstTheSpread`: never read them)
- Model-generated numbers that skip the fact lock
- Visitor-triggered model calls, free-text input to a model from the public
- User accounts, logins, collecting personal data
- Claiming affiliation with the WNBA, the NBA, any team, or the data provider
- Orange in the palette; player silhouette graphics (reads as the league mark)
- Polly generative engine for the recap (AWS documents it can occasionally speak words not in the text)
- Autoplaying audio

---

## Gate D. How it works

```
EventBridge Scheduler (morning, PT)
  -> Hunter Lambda
       1. scoreboard for yesterday (+ any missed dates since last run)
       2. for each Final game not already built:
            fetch summary -> cache raw JSON to S3 (raw/)
            build facts sheet (deterministic) -> S3 (facts/)
            Bedrock call x2 voices -> structured JSON
            fact lock -> pass: keep | fail: one retry, then drop the section
            render issue HTML + share card PNG -> S3 (site/)
       3. rebuild index pages (today, archive, by team) + Around the League
       4. write last-run marker
S3 (site/) -> CloudFront -> public URL
```

### Data source
BALLDONTLIE (`https://api.balldontlie.io`), chosen Sep 20 2026 after the compliance gate ruled out ESPN. Auth header `Authorization: <key>`, key in SSM.
- Games (finals + per-quarter scores): `GET /wnba/v1/games?dates[]=YYYY-MM-DD` (Free tier)
- Player stats: `GET /wnba/v1/player_stats?game_ids[]=<id>` (ALL-STAR, $9.99/mo per sport)
- Standings and play-by-play need GOAT ($39.99/mo), so standings movers and scoring runs are STUBs
- Never call the odds, player-prop or injury endpoints

Known risks and handling:
| Risk | Handling |
|---|---|
| Endpoint not in our tier | Block 0 tests each endpoint with the real key. Player stats (ALL-STAR, $9.99/mo) drive the spotlight, box score and The Number. Standings and scoring runs need GOAT, so both are STUBs. |
| Terms | DONE Sep 20: ESPN ruled out (terms bar automated access, AI use, dataset building; robots.txt disallows box score and play-by-play). BALLDONTLIE chosen, Section 6 permits caching, publishing, derivative works and AI outputs, no attribution required. Do not imply official or endorsed data. |
| Feed changes shape | Facts builder validates required fields. Missing field = section omitted, logged, never guessed. |
| API key handling | SSM SecureString `/full-court-press/bdl-api-key`, read at cold start, never logged, never committed. |
| Feed down during judging | Golden set + everything already built stays on S3. |
| Hammering someone else's server | Outbound rate limit from the first run: max 1 request/sec, hard cap per run. |

### Facts sheet (draft schema)
```
game_id, league, date_local, status
home: { team, abbrev, score }, away: { ... }
final_margin, overtime_periods
leaders: [{ player, team, category, value }]
player_lines: [{ player, team, min, pts, reb, ast, stl, blk, to, fg, fg3, ft, plus_minus }]
team_stats: { fg_pct, fg3_pct, ft_pct, rebounds, turnovers, ... }
runs: [{ team, points, span_start, span_end }]   // computed from play-by-play
notable: [{ type, player, detail }]               // 30-pt game, double-double, triple-double, etc.
allowed_numbers: [...]                            // every number the AI may use, incl. derived
allowed_names: [...]                              // every player and team name in this game
```

### Fact lock (the guard)
- The model returns JSON with fixed fields: `headline`, `recap`, `spotlight`, `the_number`. **Every field it returns is rendered, and every rendered field is checked.** No unchecked field for the truth to hide in.
- Check 1: every numeric token in every field must be in `allowed_numbers`.
- Check 2: spelled-out numbers ("twenty-six") are rejected outright.
- Check 3: every capitalized name-like token that matches a roster pattern must be in `allowed_names`.
- Fail: one regenerate with the failure reason, then drop that section and log it. Never publish an unchecked section.
- `the_number` is a pointer: the model picks a key from `allowed_numbers`, code renders the value.

### Game of the Night (deterministic)
Score = points for close margin (<= 5), overtime, a 30+ point game, a triple-double, a comeback of 15+ (from runs). Ties broken by later tip time. Rules live in one config file.

### Voices (original archetypes, no real people)
| Voice | Traits | MUST/STUB |
|---|---|---|
| The Call | warm, precise, poet's play-by-play rhythm | MUST |
| The Film Room | whiteboard energy, coverages and actions, nerdy joy | MUST |
| The Insider | leading pauses, "what I'm hearing," reads everything as a signal | STUB |
| The Big Picture | roster math, "zoom out," what this means in the playoffs | STUB |
Each voice = trait list + banned phrases + sentence rhythm rules + the NEVER list, in the prompt.

---

## Gate E. Model Authority Check

One model responsibility in the whole system.

```
Responsibility:      Write the recap sections in a chosen voice.
Role:                Presenter (explains deterministic facts, with voice as the creative layer)
Why probabilistic:   Voice, rhythm, and word choice are the product. The facts are not.
Stays deterministic: every number, every name, score, winner, leaders, runs, game of the
                     night, around the league, standings, dates, which games get built
Verified by:         Schema + fact lock (numbers and names against the facts sheet)
On failure:          Worst case a section reads flat or gets dropped. A wrong stat cannot
                     publish. Recovery: regenerate on the next run.
Ordinary software:   Templates can produce "X scored Y." Rejected for recaps because voice is
                     the product. Used for everything else.
```

**Second model in the system: Amazon Polly (text to speech)**
```
Responsibility:      Speak the audio script.
Role:                Presenter (reads fixed text aloud)
Why probabilistic:   Natural-sounding speech. The words themselves are not the model's.
Stays deterministic: the whole script (template over locked facts + locked headline)
Verified by:         Script is verified before synthesis; transcript shown on the page. The audio
                     itself is not machine-verified, which is why the neural engine is required
                     and the generative engine is NEVER.
On failure:          Mispronounced name at worst. Transcript is the source of truth. Polly error
                     = issue publishes without audio.
Ordinary software:   No non-model TTS worth shipping. Accepted.
```

**Wrapper test:** remove the model call. What's left is a working morning box-score zine with game of the night, around the league, archive, and share cards. Not a wrapper.

**Model choice:** candidate Claude Haiku 4.5 on Bedrock (model card exists in AWS docs). **Unverified:** lifecycle status. Block 0 confirms it's Active with `ListFoundationModels` before anything depends on it.

**Prompt injection floor:** model input is only the facts sheet JSON built by our code from structured fields. No free text from the feed (no `article`, `news`, `headlines`) and none from visitors.

---

## Gate F. Build order

Tier per project-judgment Part Three. Tier is restated inline in every Kiro prompt, with "DO NOT refactor other code."

| Block | Scope | Tier | Disposition | PASS when |
|---|---|---|---|---|
| **0** | `[THROWAWAY]` folder. Compliance gate closed Sep 20 (ESPN out, BALLDONTLIE in, see LEDGER.md). Spikes: (a) agent-to-AWS connection proof captured; (b) Lambda reads the API key from SSM and calls games, player_stats, standings and plays, recording which the tier allows; (c) Bedrock lists the chosen model as Active and returns one reply; (d) Pillow renders a text PNG inside Lambda; (e) Polly neural voices available in the same region as Bedrock, a 25-word line is about 10 s | Spike | discard (findings to ledger) | Compliance read done and all five yes/no answered. Any "no" goes to the ledger and changes this PRD before Block 1. |
| **1** | Zine page + Around the League + archive layout from **mock** facts JSON (golden fixture). Static HTML/CSS, print CSS. | Working | promote | Page renders from fixture, prints on one page, reads on a phone |
| **2** | Facts builder from cached real summaries (5 golden games, incl. one OT if available) + Game of the Night score | Working | promote | Facts match the box score for all 5 games (Kiro checks against the raw JSON) |
| **3** | Voice call + fact lock, 2 voices | Working | promote | 5 golden games x 2 voices publish, zero unchecked numbers; a planted bad number is caught |
| **4** | Share card PNG from locked text | Working | promote | Card renders for all golden games, text fits, no logos |
| **5** | Hunter on EventBridge, S3 + CloudFront publish, team filter, last-run marker, NBA stub entry | Full | promote | A scheduled run publishes last night's real games to the public URL without Shara |
| **5b** | Audio recap: Polly neural reads a template script from locked facts; player + visible transcript; `polly:SynthesizeSpeech` only | Full | promote | Live MP3s for last night, transcript matches script, no script text in logs. Cut rule: skipped if Block 5 isn't PASS by end of Sep 29 |
| **6** | 11-point checklist, cost alarm, logs audit, golden set live, submission package | Full | promote | Checklist complete, every control proven in the deployed environment (see Gate G4) |
| **7** | Wind down (written now, executed after judging). See Gate G1. | n/a | n/a | Final ledger entry written, scheduler state matches the plan |

Every block ends with a reality check on the deployed thing, not the source tree.

### Calendar (Sep 25 is the Google SF hackathon, no build that day)

| Date | Work |
|---|---|
| Sat Sep 20 | Approve PRD. Install repo walls (Gate G1). Block 0 |
| Sun Sep 21 | Block 1 |
| Mon-Tue Sep 22-23 | Block 2 |
| Wed Sep 24 | Block 3 start |
| Thu Sep 25 | Google SF. Off. |
| Fri Sep 26 | Block 3 finish |
| Sat Sep 27 | Block 4. WNBA playoffs start |
| Sun-Mon Sep 28-29 | Block 5. First scheduled live issue |
| Tue Sep 30 | Block 5b (audio, only if Block 5 passed) + Block 6 |
| Wed Oct 1 | Builder Center post, proof screenshots, dev.to draft |
| Thu Oct 2 | Buffer. Submit by noon PT, not 11:59 PM |

---

## Gate G. Guardrails

Sources: "My Agents Never Get Tired. I Do: On Satisficing," "After the Sprint: a 72-hour build retrospective (surprise, it wasn't secure)," and "Block Zero: oh no, Claude, Kiro and I over-engineered the throwaway" (all dev.to/earlgreyhot1701d). Each rule below says where it's enforced. A rule that lives only in a prompt is a request, not a guardrail.

### G1. Stop signs (satisficing)

Agents don't get tired, so the stop signs are installed on purpose, before anything exists to argue for itself.

| Rule | Enforced by |
|---|---|
| Good enough is written down first. Every block's PASS line is its standard. The first result that meets it wins. No polishing past it. | Build plan (Gate F), restated in each Kiro prompt |
| Tier is decided per block before the run, and tiers are prohibitions, not effort levels | Build plan + one inline line in every Kiro prompt |
| Block 0 lives in a `[THROWAWAY]` folder: one flat script per question, zero abstraction, no retry policies, no custom exception classes | Pre-commit hook (below) + prompt |
| Spike tier: no test files, no dependency pinning, no sync or drift scripts, no README, no files outside the spike folder | Pre-commit hook rejects manifest/lockfile changes and out-of-folder paths while the spike branch is active |
| Bounded agent runs | Tool-turn cap per Kiro session |
| Bounded spend | AWS Budgets alarm + hard per-run cap on Bedrock calls, from Block 0 |
| Steering docs don't grow forever | Size cap on `.kiro/steering/*`: something is deleted before something is added |
| No vendored modules in this build (avoids needing byte-identity and pinning controls at all) | NEVER list |
| At every QA checkpoint, two questions: PASS or FAIL? Is anything from a spike still in here? If yes, promote and re-rigor, or discard. | QA checkpoint template |
| No code is discarded before its findings ledger entry exists | Ledger file in repo |

**Block 7, wind down (decided today):**
- Dollar ceiling: if monthly AWS spend for this stack passes the Budgets threshold (set in Block 0), scheduler goes off and the site goes dormant with the archive intact.
- After the WNBA Finals: scheduler off, site and archive stay up through judging.
- Reactivation condition for the NBA stub: late Oct 2026, only if excitement is still there and spend is under the ceiling.
- Handoff notes: what's stubbed and why, in the repo README.
- Final ledger entry written whatever the result.

### G2. Security (from the 72-hour retrospective)

| Rule | What it means here |
|---|---|
| Enforce boundaries, not scary vocabulary | No keyword blocklists. The model only ever sees a facts JSON our code builds from typed fields. No feed free text (`article`, `news`, `headlines`), no visitor input. |
| Model output is still input | Every model response is schema-validated at runtime, then fact-locked, before it's rendered. Invalid = dropped, never shown. |
| No unsafe HTML paths for model values | Escaped templates only. `textContent`, never `innerHTML`, for anything model- or feed-derived. No `eval()`. |
| The strongest data protection is not having the data | No accounts, no analytics that collect personal data. The only browser storage is the visitor's chosen team, wrapped in try/catch. Raw feed JSON older than the golden set is pruned after the season. |
| Tests prove the world you modeled; production tells you it's the wrong world | Every control is proven against the deployed stack (G4), not the repo. |
| Security headers match across layers | CloudFront response headers policy: CSP, HSTS, X-Content-Type-Options, frame-ancestors. Verified on the live URL. |
| Secrets verified in the deployed environment | Kiro confirms from the running Lambda's config, not from reading the repo. No keys in the frontend. |
| No account IDs in tracked files, including the docs that describe removing them | Account-specific values in `.env` / SSM only. Scrub notes never quote the value they scrubbed. |
| Inbound rate limiting | N/A, not deferred: no API, no forms, static site. Becomes Full if any endpoint is ever added. |

### G3. Block Zero lessons

| Rule | What it means here |
|---|---|
| Compliance gate before implementation | Done Sep 20, and it did exactly its job: ESPN's terms and robots.txt killed the planned data source before anything was built on it. BALLDONTLIE replaced it. |
| Third-party libraries log things you didn't ask for | boto3/botocore debug logging off. No framework callback handlers printing model output. Checked in CloudWatch after deploy. |
| Agents report discrepancies instead of adapting silently | Standing line in every Kiro prompt: "If the spec and reality disagree, stop and report. Do not work around it." |
| Agents reason locally and don't see the calendar | Tier + date + definition of done go in the prompt, every time |
| Correct work vs appropriate work | Shara decides the tier and whether a piece deserves attention at all. Kiro decides nothing about scope. |

### G4. Proven in production (a control that has never run where it protects is not a control)

Kiro runs these against the deployed stack. Shara picks what they point at.

| Control | Proof on the live stack |
|---|---|
| Fact lock | A planted wrong number in a test facts run is rejected by the deployed Lambda, and the rejection shows in CloudWatch |
| No prompts or model output in logs | CloudWatch search after a real scheduled run returns game ids and lock results only |
| S3 private, CloudFront only | Direct S3 object URL returns access denied |
| Security headers | Live URL response headers include the full policy |
| Outbound rate limit | Run log shows spacing between API calls, the tier limit and the per-run cap |
| Budgets alarm | Alarm exists and is in OK state, threshold visible |
| Hunter runs without Shara | A scheduled run published last night's games with nobody touching it |
| Judge view | The live site on a phone and a laptop, cold browser, golden set link works |

### Kiro prompt footer (every prompt)
```
Tier: <Spike|Working|Full>. <tier prohibitions, one line>.
Definition of done: <the PASS line for this block>.
DO NOT refactor other code. DO NOT add dependencies unless this block names them.
If the spec and reality disagree, stop and report. Do not work around it.
Risk level: <low|medium|high>. Propose first. Wait for approval before implementing.
```

---

## Gate H. 11-point checklist mapping

| # | Item | Applies? | Plan |
|---|---|---|---|
| 1 | Authorization | N/A (no accounts, static site). S3 bucket private, CloudFront OAC only. | Full at Block 5 |
| 2 | Validation/sanitization | Floor from Block 2: feed data is untrusted. Escape all rendered text, no innerHTML. | |
| 3 | CORS/CSRF | N/A: no API, no forms | |
| 4 | Rate limiting | Floor from Block 0: outbound 1 req/sec, per-run cap. Inbound: CloudFront defaults. | |
| 5 | Password reset | N/A: no auth | |
| 6 | Frontend error handling | try/catch on every fetch from Block 1. Missing issue = friendly empty state, never a blank page. | |
| 7 | DB indexes | N/A: no database. S3 keys by date/team. | |
| 8 | Logging | Floor: no secrets, no full model prompts in CloudWatch. Log game ids and lock results only. | |
| 9 | Alarms | Floor: AWS Budgets alarm + Lambda timeout + per-run Bedrock call cap from Block 0. | |
| 10 | Rollback | S3 versioning on site/. Scheduler can be disabled with one switch. | Full at Block 5 |
| 11 | Prompt injection | Floor: model sees only our facts JSON, no free text. | |

---

## Gate I. Submission package (Builder Center post)
- Live URL + golden-set link judges can click
- Proof of coding agent connection (from Block 0), as a short section: the agent (Kiro), the identity it used (`fcp-kiro-agent`), a Kiro connection screenshot, a CloudTrail screenshot plus 2 or 3 exported events, a console screenshot of what the agent created, and the note that the CloudFormation stack was deployed by that same agent identity. Account id redacted throughout.
- AWS services used: Lambda, EventBridge Scheduler, S3, CloudFront, Bedrock, CloudWatch, Budgets
- Dev process: PRD-first, block order, PASS/FAIL, the fact lock story ("the AI can't make up a stat")
- Tags: `#personal-expression` `#community`
- Honest limitations section: unofficial data feed, two voices, WNBA only until NBA stub flips
- Sign-off: AI assisted. Human approved. Powered by NLP.

Wind down lives in Block 7 (Gate G1).

---

## Open questions
1. Shara's one-sentence friction for Gate B1.
2. What exact form of "proof of coding agent connection" AWS wants. Ask in the Discussion tab.
3. Data tier: if player stats return 401 on the free tier, upgrade to ALL-STAR ($9.99/mo) or cut the spotlight, box score and The Number.
7. Budgets threshold dollar amount for the wind-down ceiling.
4. Final name.
5. Standings movers: define "mover" (rank change since last run) or cut to a plain standings strip.
6. Play-by-play runs: keep in MUST or move to STUB if Block 2 runs long.
