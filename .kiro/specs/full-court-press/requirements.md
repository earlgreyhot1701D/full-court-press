# Requirements: Full Court Press

## Introduction

> **OPEN (Sep 19):** palette, name and team color are decided. Final OK on the issue sections as mocked (Req 5, 7, 8, 9) is still pending. Do not start Block 1 until this banner is removed.

A scheduled job finds last night's finished WNBA games, builds a deterministic facts sheet for each, asks a model to write recap sections in two original voices, checks every number and name the model wrote against the facts sheet, and publishes a static issue page, a share card, a daily index, an archive and an Around the League strip to S3 behind CloudFront. Visitors never trigger a model call. Steering files apply to every requirement.

Labels: MUST (build), STUB (not built, comment left), NEVER (behavior must not exist).

## Requirements

### Requirement 1: Hunter (MUST)
**User Story:** As a fan, I want last night's games to show up by morning without anyone pressing a button, so that the zine is there when I wake up.
#### Acceptance Criteria
1. WHEN the morning schedule fires THE SYSTEM SHALL read the last-run marker and fetch the scoreboard for every date from the day after the marker through yesterday (Pacific time), one date per request.
2. WHEN a game's status is Final and no issue exists for its game id THE SYSTEM SHALL build that game's issue.
3. WHEN a game is not Final THE SYSTEM SHALL skip it and leave it for the next run.
4. WHEN all games for the run are processed THE SYSTEM SHALL rebuild the today, team and archive pages and write a new last-run marker.
5. IF any single game fails THEN THE SYSTEM SHALL log the game id and reason, continue with the other games, and not advance past that game's date in the marker.
6. WHEN run with `--dry-run --date` locally THE SYSTEM SHALL read cached raw JSON, use a mock voice, and write output to `./out/` without calling S3 or Bedrock.

### Requirement 2: Fetching and caching from BALLDONTLIE (MUST)
**User Story:** As the owner, I want every request to the data source to be polite and every fetched game to be kept, so that we don't hammer someone else's server and the demo survives an outage.
#### Acceptance Criteria
1. WHEN the system makes consecutive requests to the data source THE SYSTEM SHALL send `Authorization: <key>` (key read from SSM), wait at least 1 second between requests, and stay within the account tier's requests-per-minute limit.
1b. WHEN the API returns HTTP 429 THE SYSTEM SHALL stop fetching for that run and log the cap, and WHEN it returns 401 THE SYSTEM SHALL log that the tier or key lacks access to that endpoint and continue without that data.
2. WHEN a run reaches `MAX_REQUESTS_PER_RUN` THE SYSTEM SHALL stop fetching and log that the cap was hit.
3. WHEN a request exceeds 10 seconds or errors THE SYSTEM SHALL catch it, log the URL path (no body), and treat that item as failed.
4. WHEN a game and its player stats are fetched successfully THE SYSTEM SHALL store the raw JSON under `raw/{league}/{date}/{game_id}.json` before any other processing.
5. THE SYSTEM SHALL NOT call the odds, player-prop or injury endpoints at any tier.
6. THE SYSTEM SHALL NOT state or imply that the data is official league data or that the site is endorsed by any league, team or by BALLDONTLIE.

### Requirement 3: Facts sheet (MUST)
**User Story:** As a fan, I want the numbers in the zine to be the real numbers, so that I can trust and share it.
#### Acceptance Criteria
1. WHEN a raw summary is processed THE SYSTEM SHALL produce a facts sheet with the fields defined in design.md, using only values present in the raw JSON or computed from them by code.
2. WHEN a required field is missing from the raw JSON THE SYSTEM SHALL omit the dependent section and log which field was missing, and SHALL NOT substitute a guessed value.
3. WHEN the facts sheet is built THE SYSTEM SHALL include `allowed_numbers` (every number any section may display, including derived values such as margin and percentages as displayed) and `allowed_names` (every player and team name in the game).
4. WHEN per-quarter scores are present THE SYSTEM SHALL include them (game flow is quarter by quarter). Scoring runs ARE built from play-by-play (ALL-STAR tier, confirmed Sep 23), and a run SHALL never cross a period boundary.
5. WHEN a game went to overtime THE SYSTEM SHALL record the number of overtime periods.

### Requirement 3b: Statistics counted from the play-by-play (MUST, decided Sep 23)
**User story:** As a fan, I want the stat line, because the stat line is how fans argue.

WNBA `player_stats` is GOAT-tier only. The play-by-play feed is on our tier and carries typed events
naming the player, so per-player statistics are counted from it by deterministic code.

- THE SYSTEM SHALL derive, per player: points, made field goals, made free throws, rebounds (offensive
  and defensive), assists, steals, blocks and turnovers, by walking `plays` in order and classifying on
  the play's `type` field
- THE SYSTEM SHALL NOT derive minutes, plus-minus, shooting percentages, or any attempted-shot count.
  Attempts and minutes are not present as typed events, and a percentage without a verified denominator
  is a fabricated number. These SHALL be absent, never estimated
- Player attribution SHALL be by exact match against the game's roster from the `players` endpoint. No
  fuzzy matching, no nicknames, no initials. An event naming nobody on either roster is unattributed
- **Points reconciliation (hard gate):** each team's derived player points SHALL equal that team's final
  score from the games endpoint. IF a team fails to reconcile THEN every derived figure for that game
  SHALL be omitted and the issue SHALL publish without them. Points are the only category with an
  independent source of truth, so failing this gate discredits the whole count
- **Per-category gates:** a category SHALL be omitted, for that game only, if any event in it is
  unattributed, or if it fails its own sanity check:
  - assists per team SHALL NOT exceed that team's made field goals
  - blocks per team SHALL NOT exceed the opponent's missed field goal events
  - steals per team SHALL NOT exceed the opponent's turnovers
  - a failing category is dropped alone; the rest of the line still publishes
- THE SYSTEM SHALL record, per game and per category, the attributed and unattributed event counts, so
  the owner can see how often a category is dropped. These counts SHALL NOT be shown to a visitor
- THE SYSTEM SHALL label the stat line as counted from the play-by-play, SHALL NEVER call it a box score,
  and SHALL NEVER present it as official
- Derived values enter `allowed_numbers` like any other fact and are subject to the fact lock
- Double-double and triple-double claims are permitted only when every category they depend on survived
  its gate for that game
- A model SHALL NEVER perform the counting or the attribution. This is deterministic code

**Honest limitation, stated on the About page and in the submission post:** the points total is verified
against the final score. The other categories are counted, not verified, because nothing independent
exists to check them against. An event the feed omits is an event we miss silently.

### Requirement 4: Game of the Night (MUST)
**User Story:** As a fan, I want the best game of the night on top, so that I know where to start.
#### Acceptance Criteria
1. WHEN two or more games finished on a date THE SYSTEM SHALL score each game using the rules in `gotn_rules.json` and mark the highest score as Game of the Night.
2. WHEN scores tie THE SYSTEM SHALL pick the game with the later tip time.
3. THE SYSTEM SHALL NOT use a model to choose Game of the Night.

### Requirement 4b: Team editions (MUST, decided Sep 19)
**User Story:** As a fan, I want the recap told from my team's side, so that it feels like my team's zine.
#### Acceptance Criteria
1. WHEN a game is built THE SYSTEM SHALL build two editions, one per team, from the same facts sheet. Deterministic sections (score, box score, game flow, Around the League, The Number value) are identical in both.
2. WHEN writing an edition THE SYSTEM SHALL pass the edition team's abbreviation to the model and request the recap from that team's side.
3. WHEN the edition team lost THE SYSTEM SHALL apply the losing-side tone rule: honest about the loss, credits the opponent, never mocks or blames an individual player, never comments on effort or character.
4. WHEN a visitor has picked a team THE SYSTEM SHALL open that team's edition; otherwise THE SYSTEM SHALL open the winning team's edition, with a visible toggle to the other edition.
5. Each edition has its own share card and audio script, built only from locked text and facts.

### Requirement 5: Voices (MUST: two voices; STUB: two more)
**User Story:** As a fan, I want the recap to have personality, so that it's fun to read and share.
#### Acceptance Criteria
1. WHEN an edition is built THE SYSTEM SHALL request recap sections for voices `the_call` and `film_room`, one model call per voice (4 calls per game across both editions, before retries).
2. WHEN calling the model THE SYSTEM SHALL send only the facts sheet JSON and the voice definition, with no feed free text and no visitor input.
3. WHEN the model responds THE SYSTEM SHALL validate the response against the output schema (`headline`, `recap`, `spotlight`, `the_number_key`) and discard anything that fails.
4. WHEN a run reaches `MAX_MODEL_CALLS_PER_RUN` THE SYSTEM SHALL stop calling the model and publish remaining issues without voice sections.
5. THE SYSTEM SHALL NOT name or imitate any real person in prompts or output.
6. Voices `insider` and `big_picture` are STUB entries in `voices.py`.

### Requirement 6: Fact lock (MUST)
**User Story:** As a fan, I want to know the AI cannot make up a stat, so that the fun parts are still true.
#### Acceptance Criteria
1. WHEN model output passes the schema THE SYSTEM SHALL extract every numeric token from every text field and reject the section if any token is not in `allowed_numbers`.
2. WHEN a text field contains a spelled-out number (for example "twenty-six" or "a dozen") THE SYSTEM SHALL reject the section.
3. WHEN a text field contains a capitalized multi-word name that is not in `allowed_names` and not in the allowed common-words list THE SYSTEM SHALL reject the section.
4. WHEN `the_number_key` is not a key in the facts sheet's number map THE SYSTEM SHALL reject The Number section; WHEN it is, THE SYSTEM SHALL render the value from the facts sheet, not from the model.
5. WHEN a section is rejected THE SYSTEM SHALL retry that voice once with the rejection reason, and if it fails again, drop the section and log the failing token.
6. THE SYSTEM SHALL NOT render any model-written field that has not passed the lock.

### Requirement 7: Issue page: one-pager on screen, foldable zine in print (MUST)
**User Story:** As a fan, I want a clean one-page issue I can read on my phone or print, so that it feels like a real zine.
#### Acceptance Criteria
1. WHEN an edition is published THE SYSTEM SHALL render `site/{league}/{date}/{game_id}/{team_abbrev}/index.html` (and `site/{league}/{date}/{game_id}/index.html` redirects to the winning edition) as one condensed vertical page in this order: cover block (masthead, final score, The Number, headline), audio recap player, recap with voice switcher, spotlight, box score (collapsed by default), game flow, Around the League, footer with a "Print this issue" button. (Section list pending owner approval, see banner.)
2. WHEN the visitor prints or saves as PDF THE SYSTEM SHALL lay the same content out as an 8-panel one-sheet mini zine on US Letter landscape in fold order (top row upside down: pages 5, 4, 3, 2; bottom row: 6, 7, 8, 1) using `print.css` only, with no server-side PDF.
2a. WHEN rendered at 375px wide THE SYSTEM SHALL show no horizontal scroll and keep the cover block within the first screen.
3. WHEN a voice section was dropped THE SYSTEM SHALL show the deterministic sections and the text "The writers' room passed on this one." in its place.
4. THE SYSTEM SHALL show the footer disclaimer from guardrails.md on every page.

### Requirement 8: Share card (MUST)
**User Story:** As a fan, I want an image I can post, so that I can share the zine.
#### Acceptance Criteria
1. WHEN an issue is published THE SYSTEM SHALL render a 1200x630 PNG at `site/{league}/{date}/{game_id}/{team_abbrev}/card.png` containing matchup, final score, the headline and The Number, using only fact-locked or deterministic text.
2. WHEN the headline was dropped THE SYSTEM SHALL use a deterministic headline built from the score.
3. WHEN text does not fit THE SYSTEM SHALL shrink the font to a minimum size, then truncate with an ellipsis, never overflow.
4. THE SYSTEM SHALL set `og:image` on the issue page to the card URL.
5. THE SYSTEM SHALL NOT include logos, photos or league marks.

### Requirement 9: Around the League (MUST)
**User Story:** As a fan, I want every score from last night in one glance, so that I don't miss anything.
#### Acceptance Criteria
1. WHEN the today page is built THE SYSTEM SHALL show every Final score for that date and link each to its issue.
2. WHEN the account tier includes standings THE SYSTEM SHALL show the current order and mark position changes since the previous run. Otherwise THE SYSTEM SHALL omit the standings block (STUB) and show scores only.
3. IF standings fail to load THEN THE SYSTEM SHALL show the scores only and omit the standings block without an error message on the page.

### Requirement 10: Today, team and archive pages (MUST)
**User Story:** As a fan, I want to find my team's issues fast, so that I'm not scrolling.
#### Acceptance Criteria
1. WHEN a visitor opens the site root ("All") THE SYSTEM SHALL show an INDEX of last night's slate, not an issue: the masthead, the Around the League ticker, then one card per finished game (both teams, final score, Game of the Night badge where it applies), Game of the Night first, then the rest by tip time. No recap text on the index.
1b. WHEN a visitor taps a game card THE SYSTEM SHALL open that game's issue, in the winning team's edition by default, with the edition toggle visible.
1c. WHEN a visitor has picked a team and opens "All" THE SYSTEM SHALL still show the whole slate, with that team's game pinned first and the spot color set to that team.
2. WHEN a visitor picks a team THE SYSTEM SHALL filter the index by that team's abbreviation (no model involved), show that team's most recent issue first and its older issues below, apply that team's spot color, and remember the choice in browser storage inside try/catch.
2b. WHEN the picked team did not play last night THE SYSTEM SHALL say "No game last night." above that team's most recent issue.
2c. WHEN a visitor opens an issue for a game their picked team did not play in THE SYSTEM SHALL use the default spot color.
3. WHEN browser storage is unavailable THE SYSTEM SHALL still work without remembering the choice.
4. WHEN a visitor opens the archive THE SYSTEM SHALL list all dates with issues, newest first.
5. WHEN a page's data file fails to load THE SYSTEM SHALL show "No issues here yet. Check back after the next game." and never a blank page.

### Requirement 10c: About page (MUST, added Sep 23)
**User story:** As a visitor or a judge, I want one page that tells me what this is, where the numbers
come from, and who made it, so I can decide whether to trust it.

- WHEN a visitor opens `/about/` THEN the system SHALL serve a server-rendered page, readable with
  JavaScript off, linked from the footer of every page
- The page SHALL state: what the zine is and how often it publishes; that the structure and every number
  are produced by code and the voice is written by a model; how the fact lock works, in plain language;
  that a section can be dropped and what "the writers' room passed" means
- The page SHALL credit BALLDONTLIE as the data provider in a sentence, with `BALLDONTLIE` hyperlinked to
  `https://www.balldontlie.io` (`rel="noopener"`), SHALL state that the site is not affiliated with,
  endorsed by, or associated with the WNBA, any team, or BALLDONTLIE, and SHALL NOT resell or redistribute
  raw provider data
- Every page on the site SHALL carry "Data from BALLDONTLIE" in the footer, with the same link,
  server-rendered and present with JavaScript off
- The page SHALL state the project's limitations honestly, including what is stubbed
- The page SHALL carry the owner's byline and a link to her site, and SHALL state that the project is
  non-commercial
- The page SHALL NOT contain a payment link, donation link, tip jar, advertising, tracking script, or any
  third-party embed. A support link is a STUB, deferred until after judging (Requirement 14)

### Requirement 11: Golden set (MUST)
**User Story:** As a judge, I want the demo to work whenever I look, so that I can evaluate it.
#### Acceptance Criteria
1. THE SYSTEM SHALL include at least 5 cached WNBA games from the 2026 season in `fixtures/golden/`, including one overtime game if one is available.
2. WHEN the golden set is published THE SYSTEM SHALL serve those issues at `site/golden/` and link them from the footer.
3. THE SYSTEM SHALL build golden issues through the same pipeline as live issues.

### Requirement 12: Security and operations (MUST)
**User Story:** As the owner, I want the stack safe and cheap on the first run, so that nothing lands outside the repo.
#### Acceptance Criteria
1. THE SYSTEM SHALL keep the S3 bucket private and serve only through CloudFront with Origin Access Control.
2. THE SYSTEM SHALL send CSP, HSTS, X-Content-Type-Options and frame-ancestors headers from CloudFront.
3. THE SYSTEM SHALL have an AWS Budgets budget of $10 per month filtered to the `Project=full-court-press` cost allocation tag (plus the Polly service line), alerting at 50% and 100% actual and 100% forecast, and a Lambda timeout.
3b. THE SYSTEM SHALL tag every taggable resource `Project=full-court-press`, and SHALL call Bedrock through a tagged application inference profile so model spend is attributed to the project.
4. THE SYSTEM SHALL NOT log prompts, model output text, raw feed bodies, secrets or account ids.
5. THE SYSTEM SHALL keep S3 versioning on for `site/` so a bad publish can be rolled back.

### Requirement 13: NBA league (STUB)
1. `league_config.py` SHALL contain an `nba` entry with `enabled: False` and a STUB comment: flip to True and add `nba` to `LEAGUES` when the NBA regular season starts (late Oct 2026); the BALLDONTLIE path swaps wnba for nba, same shapes.

### Requirement 14: Other STUBs
- Full player statistics (rebounds, assists, shooting splits, minutes, plus-minus). GOAT tier only for WNBA, $39.99/mo, above the budget ceiling. Revisit only if the ceiling changes.
- Support or tip link on the About page. Deferred until after judging. See LEDGER.md for the reasoning.
1. Voices `insider` and `big_picture`, email/RSS per team, downloadable PDF, fantasy playoffs zine: STUB comments only.

### Requirement 15: Wind down (MUST, executed after judging)
1. WHEN the WNBA Finals are complete THE OWNER SHALL disable the schedule and leave the site and archive up through judging.
2. WHEN monthly project spend passes $25 (wind-down ceiling) THE OWNER SHALL disable the schedule.
3. THE SYSTEM SHALL have a README section listing what is stubbed and why, and the NBA reactivation condition.

### Requirement 16: 10-second audio recap (MUST, with a cut rule)
**User Story:** As a fan, I want a quick spoken recap, so that I can get the result without reading.
#### Acceptance Criteria
1. WHEN an issue is published THE SYSTEM SHALL build an audio script of at most 30 words from the facts sheet and the fact-locked headline only: final score, overtime if any, the headline, and the top scorer's points. No model writes new text for audio.
2. WHEN the script is built THE SYSTEM SHALL call Amazon Polly `SynthesizeSpeech` with the neural engine and `POLLY_VOICE`, and store the MP3 at `site/{league}/{date}/{game_id}/{team_abbrev}/recap.mp3`.
3. WHEN the issue page renders THE SYSTEM SHALL show an audio player with `preload="none"`, no autoplay, and the exact script as a visible transcript.
4. IF Polly fails or `MAX_AUDIO_PER_RUN` is reached THEN THE SYSTEM SHALL publish the issue without the player and log the game id.
5. THE SYSTEM SHALL NOT use the Polly generative engine for this feature.
6. Cut rule (decided Sep 19): IF CHECKPOINT 5 has not passed by end of day Sep 29 THEN the audio block is skipped and this requirement becomes a STUB.
