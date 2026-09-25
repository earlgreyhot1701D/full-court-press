# Text on the team colour: decided at render time, never in JS

## The bug this fixes
`styles.css` carries `--on-spot`, the colour of text sitting on a team's spot colour, and a
`:root[data-lowc="1"] .spot-surface` escape hatch. Nothing ever set either one. `app.js` only wires the
team picker. So every page rendered ink-on-team-colour regardless of the team, and on the dark teams
(Wings navy, Mercury purple, Lynx blue, Storm green, Sun red, Aces red, Tempo bordeaux) the masthead
kicker, the headline block and the highlighted Around the League row were invisible: dark text on a dark
field, roughly 1.2:1.

## Why it cannot live in JavaScript
Requirement 10d and the no-JS baseline say the site works with JavaScript off. A contrast fix that runs
in the browser fails exactly the reader we promised to serve, and it also flashes unreadable text before
it corrects itself. The team is known when the page is built. Decide it there.

## What the renderer must do
For each page, with that page's spot colour:

1. Compute the WCAG relative luminance of the spot colour, of `--paper` (`#F4EEE2`) and of `--ink`
   (`#1E1B18`).
2. Compute the contrast ratio of paper-on-spot and of ink-on-spot.
3. Emit `data-on-spot="paper"` or `data-on-spot="ink"` on the `<html>` element, whichever ratio is
   higher.
4. If the winning ratio is still below 4.5:1, ALSO emit `data-lowc="1"`. The existing
   `.spot-surface` rule then pulls text off the colour entirely: card background, ink text, colour kept
   on the border. No team currently needs this; it exists so an unverified expansion colour cannot ship
   an unreadable page.
5. Record the chosen value and the ratio in the run log, so a bad colour is visible in the output
   rather than only on the page.

This is a dozen lines of pure Python, no dependency. It belongs next to the other deterministic helpers,
not in the template.

## Expected results for the current table
Verified against the mockup's own reporting:

| Team | Spot | Text | Ratio |
|---|---|---|---|
| DAL | `#0C2340` | paper | 13.7:1 |
| NY | `#6ECEB2` | ink | 9.1:1 |
| GS | `#B896D4` | ink | 6.8:1 |
| LV | `#BA0C2F` | paper | 5.7:1 |
| CHI | `#418FDE` | ink | 5.1:1 |
| default pink | `#FF48B0` | ink | 5.6:1 |

The default in CSS is ink, which suits the pink. Every team page must set the attribute explicitly
rather than relying on that default.

## Test for it
A rendering test that walks all 15 teams, renders one page each, and asserts the chosen text colour
reaches 4.5:1 against that team's spot colour. This is the check that catches a new team's colour being
added without anyone looking at the page.
