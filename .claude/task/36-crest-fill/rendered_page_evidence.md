# Rendered evidence — a crest fills its spot, with no tile behind it

## Instrument

Computed style and box geometry, read in the Claude desktop app's Browser pane from this branch's
Astro dev server (`preview_start` v2). The pane's screenshot action does not work in this setup, so
nothing here is a picture. The viewport was emulated at 375px and 280px (`resize_window`), the
colour scheme at dark and light, and the light theme set with `data-theme="light"` on the body. Each
spot was read with `getComputedStyle` (`background-color`, the four border widths, `color`) and
`getBoundingClientRect`.

Remote images do not load in the pane. The `img` boxes were measured, the badges were not seen.

## Pages

- Team page `/en/teams/1-fc-koln/`: 375px dark; 280px light.
- Player page `/en/players/a-pavlovic-328033/`: 280px light and dark.
- Match page `/en/2-bundesliga/matches/2026-11-20-arminia-bielefeld-vs-1-fc-magdeburg/`: 280px and 375px light.

## Result

| Spot | Count (largest page) | Not bare | `img` box equals the spot |
|---|---|---|---|
| `.crest` (52px) | 2 | 0 | 1 of 1 where an image is present |
| `.crest.xs` (24px) | 78 | 0 | 78 of 78 |
| `.pphoto` (34px) | 28 | 0 | not applicable: no image, initials in ink |

No page scrolled horizontally at 280px or 375px. The player page's large crest carries no image and
shows its initials in ink with no fill.
