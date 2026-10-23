# Verification — the shared Filter bar

Built locally with `npm run build` in `site_v2` on the committed sample: exit 0, the site's tests
pass (with `filterBar.test.mjs`), audit-seo checks 2,269 pages OK, check-built-pages checks 1,644
match pages and 15,606 match rows OK. The build was served over HTTP and measured in the browser,
each page in an iframe of the given width with the scrollbar hidden as on a phone; at 375px every
offered combination was set through the radios and the rows left on screen were counted.

criteria_demonstrated:
  - Competitions (EN, DE, FI) offers type all|club|national and region all|UEFA|CONMEBOL|CONCACAF|CAF|AFC|OFC|FIFA; the Matches page offers region all|UEFA|CONMEBOL|CONCACAF|CAF|AFC and no type filter, because only clubs play that day; the Matches day page of 21 Aug 2026 has one region and shows no bar, and that of 26 Sep 2026 offers type all|club|national and region all|UEFA|CONCACAF.
  - Every offered combination shows rows: Competitions 23 of 23 in each language, the Matches page 6 of 6, 26 Sep 7 of 7 with 2 impossible combinations removed; none leaves the page empty.
  - Forms by width, 280 to 1440px: Competitions stacked dropdowns up to 430px and buttons from 700px (FI side-by-side dropdowns at 700px, buttons from 768px); the Matches page one dropdown up to 430px and buttons from 700px; 26 Sep stacked dropdowns at 280px and buttons from 375px. No render of the 81 scrolls sideways, which closes the DE filter-row exception left at 280px.
  - In every combination set, each dropdown's value equals its checked radio (0 mismatches).
  - The dropdowns' first options read All types / All regions (EN), Alle Arten / Alle Regionen (DE), Kaikki tyypit / Kaikki alueet (FI).
  - `python scripts/check_design_inventory.py --dist site_v2/dist`: 24 pages × 3 viewports × 3 languages, 174 renders, 0 failures and 0 warnings, with the new Filter bar, Filter dropdown and Fitted block (`.fbar`, `.selbar`) rows.
