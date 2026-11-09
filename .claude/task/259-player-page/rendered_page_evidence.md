# Rendered page evidence — the Player page

## The design check, every tab

`npm run build` in `site_v2` (the committed sample), then `scripts/check_design_inventory.py --no-mocks` over every
built page, every tab opened, at 280, 320, 360, 375, 700 and 1010px in EN, DE and FI (Windows):

- **Player page and Player pages:** scroll 0, overflow 0, split 0, overlap 0, classes 0; no element failure.
- **Every other built page:** each count equals its pin in `baseline.json`; no pin moves, so neither baseline changes.
- **The run's failures** are the two that every local run of main shows too: the Matches day page measured empty on
  this machine, pinned as its Fold and Match row score misses, and the root `index.html` with no inventory row.

## Player links on the built pages

A sweep of every built page outside the Player pages, in EN, DE and FI, reading each player row (`.lrow > .plrow`)
and the player id in its photo:

- **Linked:** 306 rows of a player whose page this build makes link to that page's slug in the page's language.
- **Never a dead link:** 0 rows link to a player without a page.
- **Not linked:** 18 rows of such players, all in the line-ups of played matches (`MatchLineups.astro`), which this
  page does not link.

## Build at full scale

The Player page state with every player's page: 57,423 pages, built with the hyphen step at 741 MB peak memory
and 431 s and 378 s on two runs on this machine.

## In the Browser pane

Method: the dev server (`npm run dev` in `site_v2`, the committed 72-player sample) in the Browser pane. Each
page loads in a same-origin iframe at the listed width with no border. Every tab is opened in turn, and a resize
event lets `fitBlocks.mjs` mark each block. Per tab it records:

- **Sideways scroll:** the document scrolls wider than the window.
- **Overflow:** any element past the window's right edge.
- **Clipped text:** text cut by its box.
- **Split word:** a word whose letters sit on two lines; a soft hyphen counts as a break point.
- **Tab line count:** how many lines each tab label takes.
- **Compared with last season:** a head row in each group, stripes from row 2, names at weight 600, each name at the row's left edge, 26px from the group heading to the first line of the table.

| Player | Why | EN | DE | FI |
|---|---|---|---|---|
| H. Kane (184) | club and national team, outfield | 280, 375, 1010 ok | all six widths ok | all six widths ok |
| N. Atubolu (178768) | goalkeeper | — | 280, 320, 1010 ok | — |
| Tomás Araújo (161939) | national-team squad member with 0 minutes | — | — | 280, 375, 1010 ok |
| F. Thauvin (1922) | long club and competition names | 280, 320, 360 ok | — | — |
| Vitinha (128384) | Paris Saint-Germain | — | 700, 1010 ok | 1010 ok |

- **Vitinha:** "Saint-Germain" stays whole at every width in every language; the build keeps a hyphen-joined word in one piece (#249).
- **Tabs:** the shared tab is on one line at every width in every language, "Nationalmannschaft" (DE) and "Maajoukkue" (FI) included. The gap above the tab bar is the same as the Team page's (0px box gap at 280 and 1010px).
- **Cards (Kane):** the block takes the first form where every card holds its number and its longest word.

  | Width | EN | DE | FI |
  |---|---|---|---|
  | 280 | 2 across | 3 across | 2 across |
  | 320 | 2 across | 3 across | 3 across |
  | 375 | 3 across | 3 across | 3 across |
  | 700 | 6 in one row | 6 in one row | 6 in one row |
  | 1010 | 6 in one row | 6 in one row | 6 in one row |
