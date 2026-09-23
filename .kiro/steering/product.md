# Product: Full Court Press

Full Court Press: the morning after a WNBA game, fans get a zine for that game: a printable issue page and a social share card. Stats are deterministic. Voice is AI. The AI cannot publish a number or a name that is not in the box score.

Built for the AWS Builder Center "Zero to Shipped" hackathon. Due Oct 2 2026, 11:59 PM PT (submit by noon PT). Category `#personal-expression`, lane `#community`.

Who it's for: WNBA fans who want last night's game in their team's voice by morning, without hunting for a recap that may never come for their team. Draft by Claude, Shara to edit into her own words.

Second audience: the Zero to Shipped judges (AI scoring first, then a human panel). What they should see in 30 seconds: a live site with last night's real games, two editions per game, and the promise that the AI cannot publish a number the box score does not support.

## What a visitor sees
- All (home): last night's whole slate as an index. Masthead, score ticker, one card per game with both teams and the final, Game of the Night first. No recap text here.
- Tap a game: that game's issue, opening in the winning team's edition, with a toggle to the other team's edition
- Pick a team: the slate stays, that team's game pins to the top, the page takes that team's color, and the choice is remembered in the browser
- Issue page: headline, 10-second audio recap with transcript, recap in a chosen voice, player spotlight, The Number, box score, game flow, Around the League, print button, share card
- Print: the same issue laid out as an 8-panel foldable mini zine
- Team page: that team's issues newest first. Archive: past issues by date

## What never happens
No real media personalities, no logos or player photos, nothing about players' bodies, personal lives or injuries, no betting content, no visitor-triggered AI calls, no accounts, no claimed affiliation with the WNBA, the NBA, any team, or the data provider.

## Leagues
- WNBA: MUST (in season, playoffs start Sep 27 2026)
- NBA: STUB (config entry disabled, flip late Oct 2026)

Design source of truth: `design/full-court-press-mockup.html`. That file defines the palette, type, spacing, section order and component look for the issue page, and `design/card-*.png` define the share card. Match it. Do not invent a new look, and do not use `design/reference.html` (the old Luka Fit Index page, superseded Sep 19, kept only for history).

Full PRD: `PRD.md` in the repo root. If this file and the PRD disagree, stop and report.
