# Rendered page evidence — one page width

What was checked, how, and at which widths:

- `scripts/check_design_inventory.py --dist site_v2/dist`: every built page and mock in the block
  standard's Pages table at 375, 700 and 1010px in EN, DE and FI. 0 failures; 30 warnings, the
  same as main's build, all the proposed Header row at 700px. The same check on main's build fails
  the new Page width row 90 times.
- Browser pane, DOM and layout readings on the built `site_v2/dist` and on main's build, both over
  HTTP: 249 pages in EN, DE and FI, each in an iframe 375, 700, 800, 1010 and 1440px wide (1,245
  loads per build). Read: the bounding boxes of `.inner`, `.header-in` and `.footer-in`, the page
  height, `scrollWidth` against the viewport, the header row's own overflow, and any element inside
  `.inner` past the screen edge.
- Results: at 1440px every approved page shows the three boxes at 960px on one left edge; the Team
  and Player pages read as on main at every width; at 375px every page reads as on main; no page
  scrolls sideways or overflows its header at 700–1440px.
- Obtained: DOM and layout measurements. No screenshot (the pane's screenshot fails on this site).
