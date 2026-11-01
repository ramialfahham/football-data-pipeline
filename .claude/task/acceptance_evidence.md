# Verification — the match row's tag on narrow screens

Read on the committed sample build of `site_v2`, 2026-11-01. Details in `rendered_page_evidence.md`.

criteria_demonstrated:
  - Every built page whose match rows carry a tag was measured in headless Chromium: 108 pages (Home, the Bundesliga matchdays and 34 Team pages per language), 49 tagged rows per language, at 280, 360, 560, 768 and 1010px in EN, DE and FI. No tag box meets a team name's text box or the kick-off on any, no tagged row's names run past their column (`.sides` scrollWidth equals clientWidth on every row) and no page scrolls sideways: 0 defects in 1,620 page views. Before the change the same build had 52 failing page views at 280px.
  - At 280px EN 13, DE 29 and FI 37 of the 49 tagged rows take the narrow form, the tag on its own line at the row's left edge directly above the home team (FI Home: "Huippuottelu" 16.0–113.8 × 379.5–396.5px, "FC Groningen" from 404.1px down; DE Team page: "Nächster" 16.0–88.6 × 1110.8–1127.8px, "Borussia Mönchengladbach" from 1132.8px down); the others keep the tag before the kick-off. At 360, 560, 768 and 1010px every tagged row keeps the wide form (at 1010px FI Home: "Huippuottelu" 792.3–890.0px, the kick-off from 916.0px). The design check's Fitted block assertion finds every visible tagged row marked fit-one or fit-two at every measured width.
  - block_standard.md's Tag row adds "Narrow, a row's tag takes its own line above the home team, left-aligned" and the narrow-screen fix as a source; its Fitted block row adds `.fxrow:has(.topmatch)`. `check_design_inventory.py --no-mocks`: 99 renders at its default widths and 165 renders at 280, 360, 560, 768 and 1010px, 0 failures, 0 warnings each.

`npm run build` in `site_v2`: node tests and page-spec check pass, 2,271 pages built, SEO audit OK on 2,272
pages, built-pages check OK. The seven offline gates (the six fast gates and `check_page_css.py`) pass.
