# Rendered page evidence — Home rebuilt to its approved design

What was checked, how, and at which widths:

- `scripts/check_design_inventory.py --dist site_v2/dist`: every built page in the block
  standard's Pages table at 375, 700 and 1010 px in EN, DE and FI. 0 failures; Home's Expect row
  (Block heading, Block explainer, Competition group head, Date heading, Match row kick-off, Match
  row zone, Board name, Search field, Search button) is met at every width.
- The same check on the approved render `design-mocks/renders/home_2026-09-17_02.html`: the
  render itself misses two ruled elements (no 2px line under its competition head, its press tint
  equal to its hover tint); the built Home passes both.
- Browser pane on the `v2` dev server, `/en/`, read through the DOM and computed styles: 31
  competition groups in the served order, each head with crest, name, chevron and a 2px bottom
  border; a date heading per day, inside the fold too when the day changes and not repeated when
  it continues; 3 rows before "Show all {n}"; 285 linked rows, 24 Top match tags; 8 boards of 7
  rows with rank 1 first, the player boards with the club under the name, the team boards without
  a sub-line; both intros 13px muted.
- The fold's divider, computed with every fold open: the 3 of 23 folds that open on a new day
  carry the 1px divider on the date heading and 0px on its first match; the other 20 carry it on
  their first row, as before. The Matches page folds, which hold no date heading, are unchanged;
  the design check passes them at every width.
