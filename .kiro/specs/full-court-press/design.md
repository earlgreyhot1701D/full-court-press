# Design: Full Court Press

> **OPEN (Sep 19):** palette, name and team color are decided. Final OK on the issue sections as mocked (Req 5, 7, 8, 9) is still pending. Do not start Block 1 until this banner is removed.

## Overview
One SAM stack. One Lambda (the hunter) on a morning EventBridge schedule. One private S3 bucket. CloudFront in front of `site/`. Bedrock for the voice sections only. Everything a visitor sees is a static file.

```
EventBridge Scheduler (morning, America/Los_Angeles)
  -> hunter.handler
       state.read_marker()
       for date in dates_to_check:
         espn_client.scoreboard(league, date)          # rate limited, capped
         for game in finals not yet built:
           raw   = espn_client.summary(league, id)  -> cache.put_raw()
           facts = facts.build(raw)                 -> cache.put_facts()
           for edition in [home_abbrev, away_abbrev]:        # team editions
            for voice in [the_call, film_room]:
             out = voice_client.write(facts, voice) # Bedrock Converse, capped
             out = output_schema.validate(out)      # None if invalid
             res = fact_lock.check(out, facts)      # pass | fail(token)
             retry once on fail, else drop section
           html = render.issue(facts, voices)
           png  = card.render(facts, locked_headline)
           mp3  = audio_client.speak(audio_script.build(facts, locked_headline))  # neural, capped
           publish.issue(html, png)
         gotn  = game_of_night.pick(all facts for date)
         strip = league_strip.build(scoreboard, standings)
       publish.indexes(today, teams, archive)
       state.write_marker()
S3 site/ -> CloudFront (OAC, headers policy) -> public URL
```

## Components

### league_config.py
```python
LEAGUES = {
  "wnba": {"enabled": True,  "espn_path": "wnba", "label": "WNBA"},
  "nba":  {"enabled": False, "espn_path": "nba",  "label": "NBA"},
  # STUB(full-court-press): NBA. Set enabled True and add "nba" to LEAGUES env
  # when the NBA regular season starts (late Oct 2026). Path swaps wnba -> nba, same shapes.
}
```

### Data source: BALLDONTLIE
Chosen Sep 20 2026. ESPN was ruled out by the compliance gate: the Disney/ESPN terms bar automated access, AI use and dataset building, and www.espn.com robots.txt disallows box score and play-by-play paths for every crawler. BALLDONTLIE's terms Section 6 expressly allow caching, publishing, derivative works and AI outputs, with no attribution required. Ledger entry records the switch.
- `GET /wnba/v1/games?dates[]=YYYY-MM-DD` gives finals plus per-quarter scores (Free tier)
- `GET /wnba/v1/player_stats?game_ids[]=<id>` gives player lines (ALL-STAR tier, $9.99/mo per sport)
- `GET /wnba/v1/standings` and `GET /wnba/v1/plays?game_id=<id>` need GOAT ($39.99/mo), so standings and scoring runs are STUBs
- Auth header `Authorization: <key>`, key from SSM. Cursor pagination (`meta.next_cursor`, `per_page` max 100).
- Tier table above is the published NBA one. Block 0 confirms it per endpoint for WNBA with the real key.

### bdl_client.py
- `games(league, yyyy_mm_dd) -> dict | None`, `player_stats(league, game_id) -> dict | None`, `standings(league) -> dict | None`, `plays(league, game_id) -> dict | None`
- Module-level last-request timestamp enforces >= 1 s spacing. Counter enforces `MAX_REQUESTS_PER_RUN`.
- 10 s timeout. All exceptions caught, logged with URL path only, return None.
- Never calls the odds, player-prop or injury endpoints. 401 means the tier lacks that endpoint: log it, return None, carry on without that section. 429 means stop fetching for this run.
- The key comes from `secrets.py` (SSM SecureString `/full-court-press/bdl-api-key`, or `BDL_API_KEY` locally) and is never logged.

### facts.py (pure)
Input: the game dict plus its player_stats rows. Output: facts sheet dict:
```
game_id, league, date_local, season_type, tip_time_utc, status
home: {team, abbrev, score}, away: {team, abbrev, score}
winner_abbrev, final_margin, overtime_periods   // = game.period - 4 when period > 4. Confirmed Sep 24
                                     // on game 25014 (period 5). Cross-check: max play period must agree;
                                     // if the two disagree, omit overtime_periods and log both values.
leaders: [{player, team_abbrev, category, value}]
player_lines: [{player, team_abbrev, pts, fgm, ftm, oreb, dreb, reb, ast, stl, blk, to,
                source: "play_by_play"}]
                                     // Counted by code from plays. No min, no plus_minus, no percentages,
                                     // no attempts. A category that failed its gate is absent, not zero.
                                     // The whole block is absent if points did not reconcile.
reconciled: bool                     // false -> every derived-scoring section is omitted
quarters: {home: [q1..q4, ot...], away: [...]}   // from the PLAYS, not the games endpoint, which
                                     // carries only the final (Sep 24). zine.quarters, walked in true
                                     // game order; must add up to the final, and None if not.
runs: [...]                          // built from plays (ALL-STAR tier, confirmed Sep 23)
standings_line: {abbrev: {wins, losses, conference, conference_rank, place}}
                                     // filtered to the game's season. The API's `playoff_seed` is
                                     // conference rank for every team, so it is published as a place
                                     // ("6th in the East"), never as a seed. zine.league_strip.
notable: [{type, player, detail}]    # points-based only now: 20+ pts, 30+ pts, game high.
                                     # Double-double and triple-double are impossible without rebounds
                                     # and assists, and are NEVER inferred.
numbers: {key: value}                # every displayable number, named, e.g. "home_score", "margin", "lead_pts_A_Wilson"
allowed_numbers: [str]               # every numbers value as it would be displayed, plus FG strings "9-17" split to 9 and 17
allowed_names: [str]                 # full names, last names, team names, team abbrevs, city names
```
Missing required field -> that key is absent and `missing: [field]` lists it. Never a default guess.

### timeline.py (pure) . added Sep 24
The feed logs some events late (19 records across 4 of 5 golden games), filed out of sequence and
sometimes under an earlier period, carrying the scoreboard of their moment. Anything that walks the game
in sequence (runs, quarters) sorts plays into true game order first: period, then clock descending.
Counting stats does not need it; totals do not depend on order.

### runs.py (pure)
Walk `plays` in TRUE GAME ORDER (timeline.py), track score, emit runs of 8+ unanswered points. **A run never crosses a period boundary**: reset at each period start. Found Sep 20 while computing runs on the real DAL/PHX game with a naive walk, which merged a second-quarter run into the third.

### pbp_stats.py (pure) . derived scoring, added Sep 23
One responsibility: turn `plays` into per-player points. Nothing else.

```
count(plays, home, away, roster_lists) -> dict
    home / away: {"abbrev", "score"} from the games endpoint; roster_lists: {abbr: [players]}
    returns reconciled, player_lines, categories, team_points, discrepancy, unattributed,
    overtime_periods, roster_conflicts. Implemented Sep 24 in src/zine/pbp_stats.py.
```
- Walk `plays` in order once. Classify each play on its `type` field into a category (scoring, rebound,
  assist, steal, block, turnover). For scoring plays add `score_value` to the scorer.
- **A play carries no player field.** Confirmed Sep 23 against the OpenAPI spec: a play object is
  `id, game_id, order, type, text, home_score, away_score, period, clock, scoring_play, score_value,
  team`. There is no player id and no player object. Attribution is therefore TEXT-ONLY.
- The scorer is resolved by exact match of roster names (from `/wnba/v1/players?team_ids[]=`) against the
  play's `text`. No fuzzy matching, no nicknames, no initials, no partial surnames unless that surname is
  unique across both rosters for that game. An unmatched scoring play is unattributed, and unattributed
  points fail reconciliation by definition.
- **Roster, as built (Sep 24):** the players endpoint returns who is on a team NOW. A player who has
  since moved is missing from the game she played in (Jaylyn Sherrod, game 25014). So a game's roster is
  the current roster plus every name in that game's own "X enters the game for Y" lines, with the team
  taken from the substitution play. Still exact matching; a name claimed by both teams is left out.
- **Where the other stats live (Sep 24, from PLAY_TYPES.md):** rebounds and turnovers have play types.
  Assists, steals and blocks do not; they are embedded in other plays' text. `team` on a play is the
  shooter's or ball-handler's team, so the assister is on the same team and the blocker and stealer on
  the other. A blocked shot's text never says "misses", so it is counted as a miss explicitly.
- `type` is NOT enumerated in the OpenAPI spec, so the category vocabulary must be discovered from real
  data before the classifier is written. Task 2.6b requires printing the distinct `type` values across
  the golden games first. Do not guess it.
- Free throws vs field goals: `score_value` of 1 counts as a made free throw, 2 or 3 as a made field goal.
- **Points reconciliation (hard gate):** sum each team's player points and compare to that team's final
  score. Any unattributed points, or any mismatch, sets `reconciled = False` and the entire block is
  dropped. Points are the only category with an independent check, so a points failure discredits all of it.
- **Per-category gates:** each non-points category is dropped on its own if it has any unattributed event,
  or if it fails its sanity check: assists <= team made field goals, blocks <= opponent missed field goal
  events, steals <= opponent turnovers. A dropped category is absent from `player_lines`, never zero.
- `reconciled = False` means `scoring_lines` is dropped from the facts sheet entirely and the spotlight,
  the scoring line panel and any points-based Number are omitted from the issue. The issue still
  publishes: final score, quarters, runs, standings line and the voices.
- The discrepancy (expected, derived, unattributed count) is logged and surfaced in the run state so the
  owner can see how often it happens. It is never shown to a visitor as a number.
- This module never calls a model and never calls the network.

**Why the gates matter, and what they do not cover.** The fact lock proves the model only used numbers we
gave it. It cannot prove we counted right. Points reconcile against an independently sourced final score,
so a missed basket is caught by arithmetic. Rebounds, assists, steals, blocks and turnovers have no such
source: the sanity checks catch impossible values, not missing ones. An event the feed omits is an event
we miss silently, and the About page says so. That is the honest cost of not buying the box score.

**How it is labeled.** Every rendered derived figure carries "counted from the play-by-play" in the panel
heading or a footnote. The words "box score" never appear in the product. The About page explains the
method and says plainly that full statistics are behind a tier this project does not buy.

### game_of_night.py (pure)
Reads `gotn_rules.json`:
```json
{"close_margin_max": 5, "close_margin_pts": 3, "overtime_pts": 3, "thirty_pt_game_pts": 2,
 "triple_double_pts": 3, "comeback_min": 15, "comeback_pts": 2}
```
Comeback = largest deficit overcome by the winner, from `runs`/score walk. Tie -> later tip.

### voices.py
```python
VOICES = {
  "the_call":  {"label": "The Call", "traits": [...], "rhythm": "...", "banned": [...]},
  "film_room": {"label": "The Film Room", "traits": [...], "rhythm": "...", "banned": [...]},
  # STUB(full-court-press): "insider", "big_picture". Add definitions, add to VOICE_ORDER, costs 2 more calls per game.
}
```
Shared banned list: real media personalities' names, "sources say", injury talk, betting words (odds, spread, cover, parlay, lock), body descriptions, em dashes.

### voice_client.py
- Bedrock Runtime `converse`, `modelId=os.environ["MODEL_ID"]`, temperature 0.8, max tokens ~600.
- System prompt: role, voice definition, NEVER list, output JSON schema, "Use only numbers and names that appear in FACTS. Write numbers as digits. If you are unsure of a number, leave it out."
- User message: `EDITION: {team_abbrev}` + `FACTS:` + facts JSON (minus `raw`). Nothing else.
- Edition rule in the system prompt: tell it from the edition team's side. Losing-side tone rule: honest about the loss, credit the opponent, never mock or blame an individual player, never comment on effort or character.
- Returns parsed JSON dict or None. Never logs the prompt or the response text.

### output_schema.py
Required keys and types: `headline` str <= 90 chars, `recap` str <= 900 chars, `spotlight` {`player` str, `text` str <= 300}, `the_number_key` str. Extra keys -> invalid (no unchecked fields).

### fact_lock.py (pure)
```
check(out, facts) -> {"ok": bool, "sections": {"headline": ok|reason, ...}}
```
1. Numbers: regex `\d+(?:\.\d+)?` over every text field; each match must be in `allowed_numbers`. Percent signs and "-" in "9-17" handled by the regex split.
2. Spelled numbers: reject any whole-word match on a fixed list: zero through twenty, thirty, forty, fifty, sixty, seventy, eighty, ninety, hundred, dozen. "One" is allowed only in the phrases on an allowlist ("one of", "no one", "one more"); anything else rejects.
3. Names: sequences of 2+ capitalized words not at sentence start and not in `COMMON_CAPS` (days, months, "The Call", "Film Room", "Game of the Night", league names) must be in `allowed_names`. `spotlight.player` must be in `allowed_names`.
4. `the_number_key` must be in `facts["numbers"]`.
Failing section is named with the token that failed, for the retry message and the log.

### render.py
Jinja2 `Environment(autoescape=True)`. Templates in `templates/`. Nothing model-derived gets `|safe`. Returns HTML strings.

### card.py
Pillow, 1200x630. Fonts bundled in `static/fonts/` (Alfa Slab One, Archivo; both SIL OFL, license files included). Layout from the UI section below. Text fitting: shrink to min size, then ellipsis.

### audio_script.py (pure) and audio_client.py
Template, no model: `"{winner} {w_score}, {loser} {l_score}{, in overtime}. {locked headline}. {top scorer} led everyone with {pts} points."` Numbers are digits in the script; Polly reads them. Max 30 words; if longer, drop the last sentence.
`audio_client.speak(text)`: `polly.synthesize_speech(Engine=POLLY_ENGINE, VoiceId=POLLY_VOICE, OutputFormat="mp3", Text=text, TextType="text")`, try/except, returns bytes or None. Never logs the text.
Voice: Danielle or Ruth (owner listens and picks). Tiffany is generative-only, so she is out under the rule below.
Why neural, not generative: the Polly docs state the generative engine has an emergency stop against hallucinated speech that "does not provide complete protection." For a product whose promise is that nothing unchecked gets published, audio that can say words not in the script breaks the promise. Neural reads the given text.
Cost (Sep 2026 pricing, neural $16 per 1M characters): about 150 characters per edition, 2 editions per game. 6 games a night x 30 nights = 27,000 characters, about $0.43, inside the neural free tier for accounts in their first 12 months.

### publish.py
Writes `site/{league}/{date}/{game_id}/index.html`, `card.png`, and `site/data/today.json`, `site/data/teams/{abbrev}.json`, `site/data/archive.json`. Content-Type and Cache-Control set per file (HTML short, PNG long).

### state.py
`state/last_run.json` with `{league: last_complete_date}`.

## UI direction update (Sep 19, supersedes the palette and layout below where they conflict)
- Palette: xerox + pink. `--paper:#F4EEE2 --ink:#1E1B18 --mut:#6B6259 --card:#FFFBF3 --spot:#FF48B0 --spot-text:#B8156E --on-spot:#1E1B18`. Bright pink is never text on paper.
- Team color: when a fan picks a team, `--spot` becomes that team's color from `team_colors.json` (a small committed lookup, since BALLDONTLIE's team objects do not carry colors), and code picks `--on-spot` (ink or paper) by contrast ratio. If neither reaches 4.5:1 the team color is used only for borders, shadows and large display type. (Decided Sep 19: stays.) The issue page uses the fan's team color only when that team played in the game; otherwise the default pink.
- NEVER: orange in the palette, player silhouette graphics.
- Screen: one condensed page (Req 7). Print: 8-panel fold layout (Req 7.2). Visual reference: `design/full-court-press-mockup.html` (real WNBA teams, real box score from Sep 19 2026, recap copy written by hand and labeled, edition toggle), and `design/full-court-press-print-sheet.pdf`.
- Fonts self-hosted from `static/fonts/` (Alfa Slab One, Archivo 400/600/800, OFL). No Google Fonts link, so the CSP needs no outside font host.
- Masthead name: **Full Court Press** (decided Sep 19). Colophon line: "The name is a hand-me-down from an old courthouse newsletter."
- Team color: **stays** (decided Sep 19). Screen reference: `design/full-court-press-mockup.html`. Print reference: `design/full-court-press-print-sheet.pdf`.

## UI (original Luka-based direction, kept for layout patterns only)

Reference: `design/reference.html` (copied from `luka-fit-index-deploy/index.html`, same design as `apps/luka-fit-index/index.html` in hot-ar-summer-2026 PR #1). Owner to confirm this is the right reference. Reuse its tokens and patterns. Do not invent a new look.

Tokens (verbatim):
```css
:root { --purple:#552583; --gold:#FDB927; --cream:#f6efdb; --ink:#241535; --mut:#6d5f80; --card:#fffaf0; }
```
Fonts: `Alfa Slab One` (display, uppercase) and `Archivo` 400/600/800 (body), Google Fonts.

Pattern map:
| Zine element | Reference pattern |
|---|---|
| Page background | cream with ruled lines (`repeating-linear-gradient` 34/35px) |
| Masthead ("MORNING AFTER" + date) | `.hero`: purple, 8px gold bottom border, diagonal gold stripes, gold Alfa Slab title with ink text-shadow, rotated gold `.kicker` ("WNBA / ISSUE NO. n"), `.stamp` for "Unofficial fan zine" |
| Around the League | `.ticker`: ink bar, gold caps, scrolling scores, pauses on hover, static under `prefers-reduced-motion` |
| Team picker | `nav.chapters`: sticky, cream, 3px ink bottom border, team abbrevs as tabs |
| Section titles | `h2.sec` with gold `.tab` and 4px ink offset shadow |
| Issue cards on Today / team pages | `a.chap` cards, `.pill` for "GAME OF THE NIGHT" / "OT" / "PLAYOFFS" |
| Final score + The Number | `.metric` tiles (`.v` in Alfa Slab purple) |
| Headline | `.verdict` gold block |
| Recap body | `.lede` width and weight |
| Spotlight | `.card` with `.who` and `.ava` (initials, never photos) |
| Box score summary | `table.split` |
| Voice switcher | two `.tag` buttons (`.tag.hot` active, `.tag.rank` inactive), real `<button>`s with `aria-pressed` |
| "Writers' room passed" state | `.card.gone` + `.stamp-gone` |
| Footer disclaimer + how it's made | `footer.honesty` |

Accessibility: visible focus rings, buttons are buttons, contrast of gold-on-purple and ink-on-cream kept as in reference, `prefers-reduced-motion` honored, numbers use `font-variant-numeric: tabular-nums`.

Print (`print.css`): hide nav, ticker, voice switcher and buttons; show the active voice only; drop box shadows and background stripes; fit US Letter.

Share card proof (Sep 20): rendered for real with Pillow at 1200x630 using the bundled TTFs, one per edition, plus a stress case (over-long headline and a pale team color). Shrink-then-ellipsis and the ink/paper contrast pick both behaved. Files: `design/card-wings.png`, `design/card-mercury.png`, `design/card-stress.png`. Layout proven locally, NOT yet in Lambda (Block 0 spike 0.6 still owns that question). Card layout, top to bottom: ink band with masthead and date, winner over loser score block, The Number tile at right, headline block in the edition team's color, footer disclaimer.

Share card (1200x630): cream background with ruled lines, purple top band with gold 8px rule, masthead kicker, matchup + final score in Alfa Slab, headline in a gold verdict block, The Number as a metric tile, footer line "full court press . unofficial fan zine" (palette superseded by the xerox + pink update above). No logos, no photos.

## Connection proof (contest ship-gate requirement)
The rule: "a coding agent connected to the AWS console, with documented proof of the connection." AWS has not said what proof looks like, so the plan is layered: each layer is independent, and three of them are things a human clicking around could not fake easily.

| Layer | Artifact | Why it proves something |
|---|---|---|
| Connection | Agent Toolkit for AWS installed, `aws login` browser sign-in, profile `fcp`, AWS MCP server wired into Kiro (`AWS_MCP_PROXY_PROFILES: fcp`) | This IS the connection the contest asks about, set up the way AWS publishes it. Temporary credentials, no access keys |
| Agent side | Screenshots of the toolkit sign-in, the skill list, Kiro's `aws-mcp` config block, and a transcript of the agent running AWS commands | Shows the tool holds live credentials and is calling AWS through the official path |
| AWS side | CloudTrail events for that identity: `userIdentity`, `eventTime`, `userAgent`, `eventSource` | AWS's own log, written by AWS, not by us |
| Result side | Console screenshot of resources the agent created (the proof bucket, later the CloudFormation stack) | The connection did real work |
| Narrative | Ledger entries and the Builder Center post section "how the agent was connected" with timestamps that line up with CloudTrail | Ties the artifacts together for a judge reading quickly |

Kept in `proof/`. Account id redacted in every artifact. The same evidence gets richer as the build goes on: by Block 5 the CloudFormation stack itself was created by the agent identity, which is the strongest single item.

## Billing and tagging (so the project shows up on its own in Billing)
- Stack name `full-court-press`. Resource names prefixed `fcp-`.
- Tags: `Project=full-court-press` on every taggable resource. In SAM: `Globals` tags for functions plus explicit `Tags` on the bucket, distribution, schedule, role, and `sam deploy --tags Project=full-court-press` so stack-level tags propagate where supported.
- Bedrock: create an application inference profile with `AWS::Bedrock::ApplicationInferenceProfile` (`ModelSource.CopyFrom` = the model or system inference profile confirmed in Block 0), tagged `Project=full-court-press`. `MODEL_ID` = that profile's ARN. Plain model-ID calls cannot carry a cost tag, so this is required.
- Polly: `SynthesizeSpeech` calls cannot be tagged. The budget also includes the Polly service line. This is only accurate while nothing else in the account uses Polly; if something does, note it in the ledger.
- Owner: activate `Project` under Billing > Cost allocation tags. A new tag key can take up to 24 hours to appear and up to 24 hours more to take effect, and costs before activation are not tagged. The Block 0 spike resources carry the same tag so the key shows up early.
- Budget: $10/month alarm (50% and 100% actual, 100% forecast). Wind-down ceiling $25/month: owner disables the schedule (Block 7).

## Security design
- S3 private, OAC, bucket policy allows CloudFront distribution only.
- CloudFront response headers policy: `Content-Security-Policy: default-src 'self'; style-src 'self' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; img-src 'self' data:; script-src 'self'; media-src 'self'; frame-ancestors 'none'`, HSTS, `X-Content-Type-Options: nosniff`, `Referrer-Policy: strict-origin-when-cross-origin`.
- `app.js`: fetch JSON with try/catch, build DOM with `createElement` + `textContent`. localStorage read/write in try/catch, key `fcp.team`.
- Lambda role: `s3:GetObject/PutObject` on the bucket prefixes, `bedrock:InvokeModel` on the one model, logs. Nothing else.
- Budgets alarm (owner sets amount). Lambda timeout 5 min. `MAX_MODEL_CALLS_PER_RUN` 60.
- Loggers: `boto3`, `botocore`, `urllib3` at WARNING.

## Error handling
| Failure | Behavior |
|---|---|
| BALLDONTLIE request fails | log path and status, skip item, marker does not advance past that date |
| 401 on an endpoint | that section is omitted (standings, runs), logged once, the rest of the issue still publishes |
| Required field missing | section omitted, `missing` logged |
| Model call fails or schema invalid | treated as lock fail: retry once, then drop section |
| Lock fails twice | section dropped, "writers' room passed" state |
| Standings fail | scores-only strip |
| Frontend JSON fails | friendly empty state, never blank |

## Testing (Working tier: happy path + known edges)
- `facts`: golden games produce expected scores/leaders; missing field case; OT case
- `runs`: a known run in a golden game
- `game_of_night`: tie-break by tip time
- `fact_lock`: clean output passes; planted wrong number fails; "twenty-six" fails; unknown name fails; bad `the_number_key` fails
- `output_schema`: extra key rejected
