# Rendered page evidence — key metrics in the catalogue, cards as totals

What was checked, how, and at which widths:

- `npm run build` in `site_v2` on the committed sample: 2,269 pages audited, 1,644 match pages and
  15,606 match rows checked. The 548 built match pages in each of EN, DE and FI were searched for
  the two removed rows' names: none carries them.
- `scripts/check_design_inventory.py --dist site_v2/dist`: every built page and mock at 375, 700
  and 1010px in EN, DE and FI, 0 failures and 0 warnings.
- The page layout does not change: only which rows the served list holds.
- Obtained: build output and text searches of the built pages. No screenshot (the pane's
  screenshot fails on this site).
