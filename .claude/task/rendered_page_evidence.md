# Rendered page evidence — metric names on screen come only from the catalogue label

What was checked, how, and at which widths:

- A local build of a copy of the branch on the committed sample, served locally and opened in the
  browser pane: the Bundesliga Overview and the Borussia Dortmund team page in EN, DE and FI.
- The built HTML read for the Deserved points table's heads, block name and explainer, the
  Rankings page's description, and the team page's verdict, caption, axes, tiles and last-season
  heads: the approved wording in all three languages.
- Measured at 375 and 1010px: no sideways scroll; no table head, tile or last-season head wider
  than its box. At 320px and 375px no name in a tile or a table head splits inside a word, except
  the Finnish table heads at 320px, where "Laukausero" and "ansaittuihin" hyphenate, as on the
  approved mock.
- `scripts/check_design_inventory.py --dist <local build>`: every built page and mock in the block
  standard's Pages table at 375, 700 and 1010px in EN, DE and FI: 174 renders, 0 failures and 0
  warnings.
- Obtained: the built HTML and the DOM and style measurements. No screenshot (the pane's screenshot
  fails on this site).
