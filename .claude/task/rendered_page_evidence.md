# Rendered page evidence — the Team page's Performance tab against the registry

## The design check with the Performance tab open

`npm run build` in `site_v2` (the committed sample data). The 102 built Team pages are then switched in `dist` to
open on the Performance tab: the `checked` attribute moves from `#tab-overview` to `#tab-performance`. `dist` is a
build artifact. `scripts/check_design_inventory.py --pages "Team page" --no-mocks` then runs at 280, 320, 360, 375,
700 and 1010px in EN, DE and FI.

| Rule | Main | This branch |
|---|---|---|
| Table name cell (deserved points, weight 600) | 612 fails, measured 400 | 0 |
| Metric group heading (26px to the first line of a strip row) | 612 fails, measured 10.0, 12.1 or 10.8px | 0 |
| Overflow and overlap ("Vorsaison" past its column and over "Trend") | 1,483 overflow, 746 overlap | 3 overflow (the long Gladbach title, as on main's baseline), 0 overlap |

- **What is left:** the "expected on this page" misses (Competition row, Result row and the rest) are Overview elements, which do not show while the Performance tab is open.
- **As shipped (Overview open):** the same check gives the Team page's baseline exactly: overflow 3, split 47, classes 29, Name in whole words 3.

## Overlaps, every page

The check's own count script ran in headless Chromium over every built page (`en/*/*`, `de/*/*`, `fi/*/*`) with
every tab opened, at 280, 320 and 360px. It found no overlap on any page. Before the fix, at 280px, it found 6, all
in the narrow deserved points chart: "Borussia Dortmund" over the y tick "18" and "Manchester United FC" over "6",
in all three languages.

- **Dortmund now:** at 280px the name and the difference stack centred on the dot, "+4.7" above it and "Borussia Dortmund" below it, inside the plot.
- **Other names:** a name that fits beside its dot on neither side stacks the same way; the rest keep their side.
- **Page check:** the scatter label rule in `check-built-pages.mjs` passes on all 102 Team pages.

## Geometry in the Browser pane

The dev server, the Bayern München Team page, Performance tab checked, at all six widths in EN, DE and FI:

- **Strip group headings:** each sits 26.0px above its first row's first line of text, for all 14 headings per run, with the switch off and on.
- **Compared with last season:** no head label overflows its column or overlaps the next one.
- **Deserved points:** names are weight 600.
