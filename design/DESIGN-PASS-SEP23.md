# Design pass on the Block 1 render, Sep 23

Rendered `out/` at 390px in a real browser and read every page. No console errors, no failed requests,
no horizontal scroll anywhere. The faults below were visual and would not have shown up in any test.

## Fixed on disk (in `static/styles.css`)

**1. `.gotn` selector collision. The Game of the Night card was destroyed.**
The issue mockup uses `.gotn` for the 74px circular badge on the cover. The index uses `.card.gotn` for
the featured card. Merged into one stylesheet, the bare `.gotn` rule turned the index's featured card
into a 74px circle, and its contents piled on top of each other in an unreadable heap. Scoped the circle
to `.cover .gotn`.

**2. Text on the team colour was invisible on most teams.**
`--on-spot` and the `:root[data-lowc="1"] .spot-surface` escape hatch both existed in the CSS, and
nothing ever set either one. Every page rendered ink on the team colour, so on Wings navy, Mercury
purple, Lynx blue, Storm green, Sun red, Aces red and Tempo bordeaux the masthead kicker, the headline
block and the highlighted Around the League row were dark-on-dark at roughly 1.2:1. Invisible.
This must be decided at render time, not in JavaScript, because the no-JS baseline is a requirement and
the team is known when the page is built. Full specification in `design/RENDER-CONTRAST.md`, including
the expected value for every team. The already-rendered pages in `out/` were patched so the fix is
visible now; the renderer still has to do it.

**3. A bare `footer {}` rule was painting the light footer dark.**
Same merge collision. The issue mockup's dark footer band is an element selector, so it also hit the
index's `.sitefoot`, giving ink-coloured links on a near-black field. Every footer link on the site was
invisible, including the BALLDONTLIE credit that the Attribution guardrail requires be visible.

**4. Game flow run lines.** The right column was 52px, so "PHX 12" wrapped onto two lines. Widened, set
`white-space:nowrap`, and indented the run line so it reads as a child of the quarter above rather than
a peer.

**5. No focus states anywhere.** Nothing in the lifted CSS had one, and the team picker and the edition
toggle are the first two things a keyboard user reaches for. Added a visible outline in the spot text
colour.

**6. Added a reduced-motion guard.** The zine tilts things a degree or two by design; that character
stays, but anyone who asked their system for less motion now gets it.

## For the renderer, not fixable in CSS

**7. Dates render as `2026-09-19`.** The design says `SATURDAY, SEP 19, 2026`, in the masthead kicker and
beside "Last night". An ISO date in a masthead reads like a log line, not a zine. Format at render time
in the issue's local date.

**8. Run bars are all `width:100%`.** An 8-0 run and a 12-0 run render identically, both full width,
which makes the bar decorative rather than informative. Scale each run bar against the largest run in
that game, with a sensible minimum so a small run is still visible.

**9. A dropped stat category is silent.** On the gate-fail fixture the spotlight simply shows two stat
boxes instead of three. A reader cannot tell the difference between "this player had no assists" and
"we could not trust our assist count". A dropped voice gets "The writers' room passed on this one."; a
dropped category needs its equivalent, one line in the stat line panel, in the same plain voice:
*"Assists aren't shown for this game. The count didn't add up, so we left them out."*
This is the honesty the About page promises, and right now the page does not keep it.

**10. Naming drift.** The stat line panel's eyebrow says "STAT LINE . COUNTED FROM THE PLAY-BY-PLAY" and
its heading says "THE SHEET". Pick one name and use it everywhere, including the collapsed summary
("Show the stat line").

## Verified working
- The four fixtures all render, including the two failure states
- The About page uses the owner copy verbatim, set off by a spot rule, and reads well
- Every page has the back bar and the wordmark home link
- The footer carries the BALLDONTLIE credit and the non-affiliation line
- Both team names on an index card link to that team's edition
- 390px: no horizontal scroll, cover block within the first screen


---

# Second pass, after the render-time fixes

All four render-time items verified working in a real browser: contrast attribute correct on every page,
run bars scaled with real arithmetic (DAL's 8 and 12 point runs render at 67% and 100%), human dates, and
the dropped-category note present and in the right voice. No page errors, no horizontal scroll at 390px.

**Correction to `RENDER-CONTRAST.md`:** the default-pink figure in that file said 4.3:1. The correct WCAG
value is 5.56:1. The agent was right to keep the computed value rather than reverse-engineer the number
in the doc, and the doc has been fixed. The decision was identical either way.

## Fixed here (in `static/styles.css`)

**11. Tap targets below the WCAG 2.2 minimum.** "Read the issue", the primary action on the index, was
14px tall. Footer links were 12px, the back bar 15px. SC 2.5.8 asks for 24x24 CSS px. The voice switcher
already carried `min-height:40px`, so the pattern existed and had not been generalised. Fixed with
padding rather than type size, so nothing in the type scale moves, and reset inside `@media print`.

## Still open, for the renderer or the copy

**12. Three headings all reading "Last night".** On an issue page the recap section and the Around the
League section carry the same `h2`, and the index uses it a third time. Someone navigating by heading
hears the same label twice on one page with different content beneath it, and it is editorially muddy:
"last night" is both this game and the whole slate. Keep "Last night" for the recap, which is the voice
section and has earned the phrase, and give Around the League its own: "The rest of the slate", or
"Everything else". One word change in the template.

**13. The stat line eyebrow wraps mid-phrase** at 390px, breaking after "play-by-". Either shorten it to
"Counted from the play-by-play" without the "Stat line ." prefix, since the heading below already says
"The stat line", or allow it two lines deliberately with a tighter measure.
