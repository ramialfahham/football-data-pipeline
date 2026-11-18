# Rendered evidence — the match header's top line

## Instrument

Geometry and computed DOM, read in the browser (the Claude desktop app's built-in Chromium pane)
from this branch's Astro dev server (`npm run dev`, port 4321). The pane's screenshot action does
not work in this setup, so nothing here is a picture. Each page loaded in a same-origin iframe
the width of the emulated viewport (`resize_window`), after `document.fonts.ready`.

Data: the committed sample plus real payloads exported from prod marts on 17 Nov 2026 with the
#294 `unplayed_state` (the evidence set of `.claude/task/294-status-pages/`), removed again
afterwards.

## Pages

In EN (`matches`), DE (`spiele`) and FI (`ottelut`):

| Kind | Page |
|---|---|
| Cancelled | `fa-cup/…/2025-08-05-welwyn-vs-ware` |
| Abandoned | `la-liga/…/2026-10-10-rayo-vallecano-vs-athletic-club` |
| Awaiting result | `coupe-de-france/…/2026-11-14-stade-bordelais-vs-mazeres` |
| Postponed | `afc-champions-league/…/2026-03-09-al-ahli-jeddah-vs-al-duhail-sc` |
| Not started (committed sample) | `bundesliga/…/2026-10-18-bayer-04-leverkusen-vs-sc-freiburg` |
| Played (committed sample) | `bundesliga/…/2024-12-14-1-fc-union-berlin-vs-vfl-bochum` |

## What was checked per page

- the top line (`.mast .status-word`) present exactly on the not-started, postponed and played pages;
- the status tag in the kick-off line exactly on the four status pages;
- no element of the header outside the header's box, the visually hidden page title (`h1.vh`)
  excepted;
- the page no wider than the viewport.

## Results

| Width | Pages | Defects |
|---|---|---|
| 280px | 18 | 0 |
| 320px | 18 | 0 |
| 375px | 18 | 0 |
| 768px | 18 | 0 |

Top line read at 280px: "Match preview" / "Spielvorschau" / "Otteluennakko" on the not-started and
postponed pages. On the played sample it shows that match's own status word, "Awarded" /
"Gewertet" / "Tuomittu", as on main. There is no top line on the cancelled, abandoned and
awaiting-result pages. There the kick-off line starts 8px under the competition head; on the pages
with a top line it starts 40px under it.

A first pass flagged the postponed page as clipped at 280px. The element was the "Al-Duhail" unit
inside the visually hidden page title (`h1.vh`, 1px wide, screen-reader only), not anything drawn
on screen; that page's markup is the same on main.

## Every other match page

A match without `unplayed_state` takes the same branch as on main: "Match preview" unplayed, the
played status word once played. The committed sample carries no `unplayed_state`, so every match
page the CI builds renders as on main.
