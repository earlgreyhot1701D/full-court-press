# Team spot colors

Source: teamcolorcodes.com, fetched Sep 23 2026. One color per team, picked from that team's official
palette. The pick is the most identifiable color that still prints on cream stock, which is why a few
teams use their second color instead of the one listed first (three teams lead with a yellow that fails
contrast on `--paper`).

Not official brand assets and not an endorsement. The About page states the non-affiliation.

| Abbr | Team | Spot | Name | Note |
|---|---|---|---|---|
| ATL | Atlanta Dream | `#C8102E` | Red | |
| CHI | Chicago Sky | `#418FDE` | Blue | Yellow `#FFCD00` is listed first, unusable on cream |
| CON | Connecticut Sun | `#A6192E` | Red | Orange `#DC4405` is a secondary, not the primary |
| DAL | Dallas Wings | `#0C2340` | Navy | |
| IND | Indiana Fever | `#C8102E` | Red | |
| LA | Los Angeles Sparks | `#702F8A` | Purple | Not `#552583`, which is the Lakers' purple |
| LV | Las Vegas Aces | `#BA0C2F` | Red | Silver `#8A8D8F` fails contrast badly |
| MIN | Minnesota Lynx | `#236192` | Blue | Navy `#0C2340` is listed first but collides with DAL |
| NY | New York Liberty | `#6ECEB2` | Seafoam | Light. Expect the contrast fallback to fire |
| PHX | Phoenix Mercury | `#201747` | Purple | |
| SEA | Seattle Storm | `#2C5234` | Green | Yellow `#FBE122` is listed first, unusable on cream |
| WSH | Washington Mystics | `#0C2340` | Navy | Collides with DAL; see the collision note |
| GS | Golden State Valkyries | `#B38FCF` | Violet | **UNVERIFIED** |
| POR | Portland Fire | `#CEE5EB` | Pale blue | **UNVERIFIED** |
| TOR | Toronto Tempo | `#33476D` | Slate | **UNVERIFIED** |

## Unverified teams
teamcolorcodes.com lists only the twelve established clubs. The three 2026 expansion teams are not on it,
so their values are the mockup's originals and are guesses. Confirm from each club's own site before
Block 1 ships, or fall back to `--spot` (the pink) for any team whose color is not confirmed. Do not
invent a value.

## Collisions
Two teams share `#0C2340` and two share `#C8102E`. An issue page shows one team's color at a time, so
this only matters on the index, where several issues sit together. Acceptable. Do not resolve it by
inventing an off-brand hue.

## Contrast rule
Unchanged from the mockup: compute contrast against `--card`. Below 4.5:1, set `data-lowc="1"`, and the
color renders on shapes and borders only while text falls back to `--ink`. Deterministic, no judgment
call at render time. NY, and any pale expansion color, will exercise this path.
