# Rendered page evidence — pages hold on narrow screens

What was checked, how, and at which widths:

- `scripts/check_design_inventory.py --dist site_v2/dist`: every built page and mock in the block
  standard's Pages table at 375, 700 and 1010px in EN, DE and FI. 0 failures and 0 warnings; main's
  build gives 30 warnings, the Header row at 700px.
- Browser pane, DOM and layout readings on the built `site_v2/dist` and on main's build, both over
  HTTP: 9 page types in EN, DE and FI, each in an iframe 280, 320, 375, 430, 700, 768, 1010 and
  1440px wide with the scrollbar hidden, every tab opened (216 renders). Read: `scrollWidth`
  against the viewport, every element whose box is narrower than its longest word (measured in its
  own font), and each block's fit-one or fit-two mark.
- Results: no word splits or overruns at any width; no sideways scroll except the DE filter rows
  at 280px, left to the Filter bar; at 1010 and 1440px every element's box equals main's.
- Obtained: DOM and layout measurements. No screenshot (the pane's screenshot fails on this site).
