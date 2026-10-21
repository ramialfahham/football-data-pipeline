# Verification — one page width

Built locally with `npm run build` in `site_v2` on the committed sample: exit 0, the site's tests
pass, audit-seo checks 2,269 pages OK, check-built-pages checks 1,644 match pages and 15,606 match
rows OK. Main's build (`gitlab/main` at de1d5445) was kept beside it for comparison. Both builds
were served over HTTP and measured in the browser with each page in an iframe of the given width;
the readings are the bounding boxes of `.inner`, `.header-in` and `.footer-in`, the page height,
sideways scroll, header overflow and any element past the screen edge. The sample is 249 pages in
EN, DE and FI: every top-level page, every competition page and tab page, and samples of team,
player, match day and match pages.

criteria_demonstrated:
  - At 1440px, all 213 approved-page loads (every sampled page except the Team and Player pages, in EN, DE and FI) measure `.inner`, `.header-in` and `.footer-in` at 960px each, with the same left edge (Home EN: 231px for all three). On main's build the same Home measures content 680px at 371px under a 1100px header and footer at 161px.
  - The Team and Player pages carry `legacy-width` on the body and no other page does (checked on all 249 pages). Their readings at 375, 700, 800, 1010 and 1440px are identical to main's build: content 680px, header and footer 1100px. The test `test_the_content_column_header_and_footer_share_the_page_width` pins the two earlier widths and that only `[team].astro` and `[player].astro` pass `legacyWidth`.
  - At 375px all 249 pages read the same as on main: the three boxes, the page height and sideways scroll. The 393 readings (every page at 375px, plus the Team and Player pages at every width) give the same SHA-256 on both builds, f398a798cff6dbaa…
  - At 700, 800, 1010 and 1440px (iframe widths, scrollbar included), none of the 249 pages in EN, DE or FI scrolls sideways, overflows its header row or has an element past the screen edge. `scripts/check_design_inventory.py` at exactly 375, 700 and 1010px gives the same 30 warnings as on main, all the proposed Header row at 700px, and no new one.
  - `python scripts/check_design_inventory.py --dist site_v2/dist`: 24 pages × 3 viewports × 3 languages, 174 renders, 0 failures. On main's build the same check fails the Page width row 90 times (header and footer at 1100px), so the row measures what it claims. It is measured on every built page without `legacy-width`. The content column, which mock harnesses restyle and the row therefore cannot name, is pinned to the same width by the test above, which reads the row's value.
