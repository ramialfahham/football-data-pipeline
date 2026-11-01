# Rendered page evidence — the match row's tag on narrow screens

Read on the committed sample build (`npm run build` in `site_v2`, 2,271 pages), served from
`site_v2/dist` on the local port and opened in headless Chromium at each width.

Method: on every built page holding a `.fxrow .topmatch`, each tagged row's tag box was compared with
the text boxes of both team names and with the kick-off box, the names' column was checked for
overflow (`.sides` scrollWidth against clientWidth), and the page for sideways scroll.

- **Pages:** 108 = 3 languages × (Home, the Bundesliga matchdays, 34 Team pages carrying the Next tag); 49 tagged rows per language at every width.
- **Before** (the build without this change): 52 failing page views, all at 280px (FI 24, DE 24, EN 4); a tag on a name on 18 of them, e.g. "Huippuottelu" over "FC Groningen", "Nächster" over "Borussia Mönchengladbach"; none at 360px and wider.
- **After:** 0 failing page views of 1,620. Narrow form at 280px on EN 13, DE 29, FI 37 rows; none at 360, 560, 768 or 1010px.
- **Narrow form, 280px:** FI Home "Huippuottelu" 16.0–113.8 × 379.5–396.5, "FC Groningen" 50.0–140.8 × 404.1–424.1, kick-off 222.8–264.0; DE Team page "Nächster" 16.0–88.6 × 1110.8–1127.8, "Borussia Mönchengladbach" on two lines from 1132.8; EN matchdays "Top match" 16.0–94.5 × 1089.7–1106.7, "Bayer 04 Leverkusen" from 1114.3. Names' column 191px, nothing overflowing.
- **Wide form, 1010px:** the same rows keep the tag before the kick-off: FI "Huippuottelu" 792.3–890.0, DE "Nächster" 817.4–890.0, EN "Top match" 811.5–890.0, the kick-off from 916.0.
- **Design check:** `check_design_inventory.py --no-mocks`: 99 renders (default widths) and 165 renders (280, 360, 560, 768, 1010px), 0 failures, 0 warnings.
