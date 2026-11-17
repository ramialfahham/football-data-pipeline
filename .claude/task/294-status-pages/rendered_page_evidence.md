# Rendered evidence — status tag on the match row and the match header

## Instrument

Geometry and computed style, read in the browser (the Claude desktop app's built-in Chromium pane)
from this branch's Astro dev server (`npm run dev`, port 4323). The pane's screenshot action does
not work in this setup, so nothing here is a picture. Each page loaded in a same-origin iframe
the width of the emulated viewport (`resize_window`), after `document.fonts.ready`. On a Matchdays
page the round holding each status tag was opened (its radio checked, `change` dispatched, so
`fitBlocks.mjs` measured it). Measured per tag with `getBoundingClientRect` and `getComputedStyle`.

Data: the committed sample plus real payloads exported from prod marts (see
`acceptance_evidence.md`), removed again afterwards.

## Pages

In EN (`matches`), DE (`spiele`) and FI (`ottelut`):

- Matchdays: `/coupe-de-france/…/`, `/fa-cup/…/`, `/la-liga/…/`, `/afc-champions-league/…/`
- Match pages: `2026-11-14-stade-bordelais-vs-mazeres` (awaiting result), `2025-08-05-welwyn-vs-ware`
  (cancelled), `2026-10-10-rayo-vallecano-vs-athletic-club` (abandoned),
  `2026-03-09-al-ahli-jeddah-vs-al-duhail-sc` (postponed)

## What was checked per tag

- the tag's box inside its row's (or header's) box;
- no team name wider than its own box (`scrollWidth > clientWidth`);
- no team name box intersecting the tag box;
- the tag on one line (height at most 24px);
- in the own-line form, the tag's left edge on the row's left edge;
- the page no wider than the viewport (`documentElement.scrollWidth`).

## Results

| Width | Tags | Inline (kick-off column, `fit-one`) | Own line (`fit-two`) | Header kick-off line | Defects |
|---|---|---|---|---|---|
| 280px | 45 | 18 | 15 | 12 | 0 |
| 320px | 45 | 33 | 0 | 12 | 0 |
| 375px | 45 | 33 | 0 | 12 | 0 |
| 768px | 45 | 33 | 0 | 12 | 0 |

At 280px the 15 own-line rows are the German and Finnish Coupe de France rows: "Ergebnis ausstehend"
and "Tulosta odotetaan" (151px in German) beside two club names.

Before the `minmax(0, 1fr)` column was added for a status row, the same 280px run found 15 tags
outside their row and a page wider than the screen on the German and Finnish Coupe de France pages.
That was the measurement that led to the row tag's own-line form.

Computed style of every tag: `font-size 11px; font-weight 700; text-transform uppercase;
border-radius 4px; background-color rgb(59, 176, 114)` (the accent), the Tag rule's form.

## Where the tag does not appear

- **Team page match rows:** `asMatchRowFixture` builds them from `mart_team_fixtures` schedule
  rows, which carry no `unplayed_state`.
- **Committed sample:** its payloads carry no `unplayed_state`, so the CI builds render as on main.
