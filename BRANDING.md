# Full Court Press: brand sheet

The one place for how Full Court Press looks and sounds. If the site, the share card, the print zine, the README, or the article disagree with this file, this file wins (or gets updated on purpose).

Labels: **IN USE** means it ships today. **PROPOSED** means it's waiting on a decision.

---

## 1. What it is

**Name:** Full Court Press (always three words, title case; never "FCP" in anything a fan reads)
**Domain:** fullcourtpress.lol
**One-liner (IN USE):** The zine for last night's WNBA games. (Dropped "morning-after": it reads like Plan B.)
**Longer line (PROPOSED):** Counted stats, written in two voices, checked before they print. One page on your phone, eight panels on paper.
**Name origin:** a personal easter egg. It was the name of a court newsletter back in the day.

## 2. Color

| Token | Hex | Job | Status |
|---|---|---|---|
| Blush paper | `#FCF3F5` | Page background, with 11px pink dots | IN USE |
| Plum | `#2B1A2F` | Header, cover, ticker, footer, card bands | IN USE |
| Spot pink | `#FF48B0` | Accent: stamps, tabs, highlights, ransom tiles | IN USE |
| Deep pink | `#B8156E` | Pink text on light paper (contrast-safe) | IN USE |
| Ink | `#1E1B18` | Body text | IN USE |
| Card cream | `#FFFBF3` | Taped cards and panels | IN USE |
| Highlighter | `#F4E27A` | Highlighter marks, one ransom tile | IN USE |

Rules:
- Team color replaces spot pink on a team's edition. Plum and blush never change.
- Text on a team color is chosen at render time for contrast (design/RENDER-CONTRAST.md). Low-contrast teams fall back to ink on cream.
- Pink is an accent, not a background for paragraphs.

## 3. Type

| Face | Use | Status |
|---|---|---|
| Alfa Slab One | Headlines, scores, big numbers, drop caps | IN USE |
| Archivo (variable) | Body, UI, labels | IN USE |
| Caveat | Handwritten margin notes only | IN USE |

All three are OFL and self-hosted in static/fonts/ with their licenses. No Google Fonts calls.

## 4. The look: soft riso zine

- Riso paper: blush with pink halftone dots and light grain.
- Off-register ink: a pink shadow that sits a couple of pixels off the plum.
- Crooked taped cards, staples, rubber stamps (FINAL), highlighter, torn edges.
- Ransom-note masthead: each word its own tile, slightly rotated.
- Screen, share card, and print sheet all match. If one changes, check the other two.

## 5. Voice

Two voices, both reading the same checked facts sheet:

| Voice | Feel | For |
|---|---|---|
| **The Call** | The friend who watched it with you. Warm, fast, a little dramatic. | Fans who want the feeling |
| **The Film Room** | Quarter by quarter, evidence first. Calm and nerdy. | Fans who want the why |

Every edition is written for one side. The losing side gets respect, not a pity party.

Words we don't use: anything that claims a moment the facts don't show (dagger, buzzer-beater, final possession), plus the banned list in `src/zine/voices.py`. No betting language, no injury talk, ever.

The honest line (keep it everywhere it fits): the fact lock proves every number and name came from our facts. It doesn't prove the sentence around them is right, so we recheck and drop what fails.

## 6. Icon and social preview (IN USE)

**Favicon: A2, "F + CP tag."** A crooked pink tile with a plum F, and a small cream ransom tag reading CP on the bottom-right corner. Pulled from the masthead.

| File | Size | Job |
|---|---|---|
| `static/favicon.svg` | scales | Browser tab (modern browsers) |
| `static/favicon-32.png` | 32px | Fallback for browsers without SVG icons |
| `static/apple-touch-icon.png` | 180px | Phone home screen |
| `static/og-default.png` | 1200x630 | Social preview for the front page, archive, team and About pages |

Game pages use their own share card (`card.png`) as the social preview instead of the default.

Honest limit: at 16px the CP tag blurs into a light corner. It reads from 32px up.

Sources: the three first options and both CP versions live in `design/favicon/` with previews. The social preview's source page is `design/og-default-source.html` (it expects the fonts from `static/fonts/` next to it to re-render).

## 7. Credits and attribution

- Game data: BALLDONTLIE, credited with a link on every page.
- Not affiliated with the WNBA or any team. Team names and colors are used to label editions, not as logos. No team or league logos, ever.
- Voices: Amazon Bedrock (Claude Haiku 4.5). Audio: Amazon Polly (neural voice).
- Sign-off: AI Assisted. Human Approved. Powered by NLP.

## 8. Still to decide

- [x] Favicon: A2
- [x] One-liner: The zine for last night's WNBA games.
- [x] Default social preview (og-default.png)
- [x] README banner: `design/readme-banner.png` (1280x400)
- [ ] GitHub social preview: upload `static/og-default.png` in repo Settings
- [ ] Article cover image
