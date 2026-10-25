# Rendered page evidence — the match page's Show all metrics switch and team names

What was checked, how, and at which widths:

- `scripts/check_design_inventory.py --dist <local build>`: every built page and mock in the block
  standard's Pages table at 375, 700 and 1010px in EN, DE and FI, the Played match page now
  expecting the Metric switch and the Comparison team name. 174 renders, 0 failures and 0 warnings.
- Browser pane, DOM and style readings on the dev server: the played match Hoffenheim 2–3 Dortmund
  (EN, 1010px) and the upcoming Leverkusen vs Freiburg (DE at 375px, FI at 1010px). Read: the rows
  and group headings shown with the switch off and on, the label's text and style, the team names'
  style, the switch's right edge against the comparison's, `scrollWidth` against the viewport, the
  accessibility role and name, keyboard focus and the Space key.
- Results: the key rows only when off, every row in order when on; no sideways scroll; the switch
  ends at the comparison's right edge at both widths.
- Obtained: DOM and style measurements. No screenshot (the pane's screenshot fails on this site).
