# Verification — the shared fold

Built locally with `npm run build` in `site_v2` on the committed sample: exit 0, the site's tests
pass, audit-seo checks 2,269 pages OK, check-built-pages checks 1,644 match pages and 15,606 match
rows OK. `python scripts/check_design_inventory.py --dist site_v2/dist`: 24 pages × 375/700/1010 px
× EN/DE/FI, 174 renders, 0 failures; the 30 warnings are all the proposed Header row. Counts below
are read from `site_v2/dist`, the same in all three locales.

criteria_demonstrated:
  - Shown rows and the closed control: Home has 23 folds per locale, the Matches page 10, the 49 Matches day pages 46; in every one the fold sits after exactly 3 `.fxrow` rows and its closed label's n equals the group's row count (3 shown plus the folded ones). Labels read "Show all 5" (EN), "Alle 5 anzeigen" (DE), "Näytä kaikki 5" (FI); the chevron computes to rotate(90deg), pointing down, in the browser.
  - Opened, one list: with every fold opened in the browser (Home at 375 px, the DE Matches page at 1010 px), the gap between every two consecutive rows is 0 px and every row keeps its 1px divider, the last folded row included; the 3 Home folds that open on a new day carry the divider on the row above the date heading and none between the date heading and its first match.
  - Opened, the control: the control's top equals the last row's bottom (0 px) on all 23 Home and 10 Matches folds; it reads "Show less" (EN), "Weniger anzeigen" (DE), "Näytä vähemmän" (FI), the chevron computes to rotate(-90deg), pointing up, and a second click returns the group to 3 rows. By keyboard, Tab reaches the fold, the 2px accent focus ring draws on its control, and Space opens it.
  - No script: no page holds a `details.fxmore` or any `<details>`; no inline script on Home, the Matches page or a Matches day page names the fold; every row is in the HTML (the shown plus folded `.fxrow` counts equal n for every fold), toggled by `input.fold-in` and its `label.fold-ctl`; every fold id is unique on its page.
  - The design check measures the Fold: the block standard's Fold row now selects `.fold-ctl` and Home's Pages row lists Fold beside the Matches page and Matches day page rows; the check passes it on all three at 375, 700 and 1010 px in EN, DE and FI.
