# Rendered page evidence — the shared fold

What was checked, how, and at which widths:

- `scripts/check_design_inventory.py --dist site_v2/dist`: every built page and mock in the block
  standard's Pages table at 375, 700 and 1010 px in EN, DE and FI. 0 failures; the Fold
  (`.fold-ctl`, 13px, weight 600, ink-2) is met on Home, the Matches page and the Matches day page
  at every width. `pytest tests/test_design_inventory.py`: 46 passed.
- Browser pane on the built `site_v2/dist` over HTTP, read through the DOM and computed styles with
  the chevron's transition switched off: `/en/` at 375 px (all 23 folds) and `/de/spiele/` at
  1010 px (all 10 folds), each opened and closed: 3 rows closed, every row open with 0 px between
  rows, the control flush under the last row, the label and chevron per state, 3 rows again after
  closing; no sideways scroll at 375 px.
- Keyboard on `/de/spiele/`: Tab from the third row lands on the fold's checkbox, `:focus-visible`
  holds and the label draws the 2px accent ring; Space opens the fold and the label reads
  "Weniger anzeigen".
- The mocks that render the fold: `design-mocks/gen_home.py` with `check_home.py` (the four fold
  checks pass; its board-label check fails on main too) and `design-mocks/gen_matches_hub.py`.
