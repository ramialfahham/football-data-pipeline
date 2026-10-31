# Rendered page evidence — the Teams page

Read on the full export (3,342 teams); the committed sample (778 rows) was rebuilt and measured
again by the design check, 9 renders, 0 failures.

Method: no screenshot, which this Browser pane cannot take. The page was read in the `v2` dev server through
the DOM, with each element's bounding box and computed style, and measured in headless Chromium by
`scripts/check_design_inventory.py` on the built `site_v2/dist`.

- **Widths and languages:** `/en/teams/`, `/de/mannschaften/` and `/fi/joukkueet/` were each loaded fresh at 280, 360, 768 and 1010px, plus DE at 560px. At every one, `document.documentElement.scrollWidth` equals the viewport, so nothing scrolls sideways (768px: 753, the scrollbar).
- **Grid:** the lists' `grid-template-columns` is 1 column at 280px (248px), 1 at 560px (515px), 2 at 768px (344.5px × 2) and 2 at 1010px (448px × 2). Before the two-column cap it was three columns at 1010px (296px × 3).
- **Group head:** "England" at 17px with a 2px rule under it; its count "868 teams" / "868 Mannschaften" / "868 joukkuetta" is at the right in 13px muted. At 280px the head is 33.5px tall, on one line.
- **Filter bar:** buttons at 1010px; at 280px the two dropdowns show (`.selbar` visible) with no cut-off.
- **Filter swaps:** all 21 type × region combinations were set through the radios. Under a region, the "All regions" top lists are hidden and that region's lists show: Top clubs 10 rows for Europe, 6 for the other regions, no fold; Top national teams 10 rows with the region's fold. The National teams by region block is hidden. Clubs + Oceania is removed from the choices. Under Clubs, the national blocks are hidden; under National teams, the club blocks are hidden.
- **Fold inside the grid:** Top clubs shows 10 rows and "Show all 44" (EN), "Alle 44 anzeigen" (DE), "Näytä kaikki 44" (FI). The fold control spans both columns.
- **Heading gap:** the first top-list row's crest started 22px under the "Top clubs" heading. With the top lists' grid pulled up by the row padding, `check_design_inventory.py --pages "Teams page"` measures 14px: 9 renders (375, 700, 1010 × EN, DE, FI), 0 failures. The full built run: 11 pages, 99 renders, 0 failures.
