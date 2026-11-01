# Rendered page evidence — the Team page's strip plot and scatter labels

Read on the committed sample build (`npm run build` in `site_v2`, 2,271 pages, 34 Team pages per
language), served from `site_v2/dist` on the local port.

Method: no screenshot, which this Browser pane cannot take. Each page was read in the Browser pane
through the DOM (computed style, bounding boxes, `scrollWidth`) and, for the scatter on every Team
page, in headless Chromium with the same box measurement.

- **Views:** the Team page Performance tab (`/en/teams/bayern-munchen/`, `/de/mannschaften/…`, `/fi/joukkueet/…`), the competition page (`/en|de|fi/bundesliga/`) and Home (`/en/`, `/de/`, `/fi/`), each at 280, 360, 560, 768 and 1010px: 45 views. At every one `document.documentElement.scrollWidth` equals the viewport (768px: 753, 1010px: 995, the scrollbar), so nothing scrolls sideways.
- **Strip plot:** 33 rows, no `.rs-med`, `.rs-medv` or `.rs-k-med` node; the legend reads "Bayern München / Other Bundesliga teams" ("Übrige Klubs der Liga", "Sarjan muut joukkueet"); the right column reads "1st" (DE and FI "1.") at 15px/700 with "3.6" ("3,6") under it at 12px/400; the strip's top margin is 10px; 33 of 33 rows carry the "better" marker; no row overflows at any width.
- **Explainers:** the Team page shows the approved `teamPerfIntro`, `compDeservedExplainer` and `teamVsLeagueIntro`, the competition page the approved `compDeservedExplainer`, Home the approved `homeTopPlayersIntro` and `homeTopTeamsIntro`, in each language at each width. EN at 280px: "Bundesliga 2026/27: Bayern München compared with the other teams and with the season before, without other competitions." and "Each value is ranked against the other Bundesliga clubs this season."
- **Scatter, every Team page:** 102 Team pages (34 × EN, DE, FI) at 280, 360, 560, 768 and 1010px, 510 charts measured (narrow at 280 and 360, wide from 560): the team name's box and the difference label's box overlap on none, both sit inside the chart on all 510, and no label's box reaches the y axis line. Of the 204 built charts, 201 put the label across the dot from the name and 3 under the name.
- **Left edge:** the 3 under the name are Borussia Mönchengladbach's narrow chart in EN, DE and FI, where the label opposite the name would cross the y axis (before this placement, its box ran 44.4–61.6px over the axis at 46.1px). Now at 280px (FI) the name's box is 73.3–192.3 × 1410.6–1423.6px and "−2,5" sits under it at 73.3–93.3 × 1425.2–1438.2px, 27px clear of the axis; at 360px (EN) the boxes are 1340.6–1357.6 and 1359.9–1376.9px high.
- **Build check:** `check-built-pages` reads all 204 built scatters and passes; it fails a page whose label is neither across the dot from the name nor at least one line under it (its tests include the old beside-the-name placement).
- **Design check:** `check_design_inventory.py --no-mocks`: 11 pages × 3 viewports × 3 languages, 99 renders, 0 failures, 0 warnings.
