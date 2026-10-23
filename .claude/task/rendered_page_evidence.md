# Rendered page evidence — the shared Filter bar

What was checked, how, and at which widths:

- `scripts/check_design_inventory.py --dist site_v2/dist`: every built page and mock in the block
  standard's Pages table at 375, 700 and 1010px in EN, DE and FI. 0 failures and 0 warnings.
- Browser pane, DOM and layout readings on the built `site_v2/dist` over HTTP: the Competitions,
  Matches and two Matches day pages in EN, DE and FI, each in an iframe 280, 320, 375, 430, 700,
  768, 1010 and 1440px wide with the scrollbar hidden. Read: the bar's fit marks, `scrollWidth`
  against the viewport, the offered choices, the rows left by every offered combination, and each
  dropdown's value against its radio.
- Results: no sideways scroll; the form follows the fit; every offered combination shows rows;
  dropdowns and buttons always agree.
- Obtained: DOM and layout measurements. No screenshot (the pane's screenshot fails on this site).
