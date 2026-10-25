# Rendered page evidence — the competition page's season label

What was checked, how, and at which widths:

- A local build of a copy of the branch on the committed sample, its BL1 payload given the label
  in the copy only. The built HTML's `.meta` line read on the Bundesliga Overview, Matchdays and
  Rankings pages in EN, DE and FI: "Germany · Season 2026/27 · Regular Season - 6", "Saison", "Kausi".
  The Premier League and the World Cup have no payload in the sample and show their region only.
- `scripts/check_design_inventory.py --dist <local build>`: every built page and mock in the block
  standard's Pages table at 375, 700 and 1010px in EN, DE and FI: 174 renders, 0 failures and 0
  warnings.
- Obtained: the built HTML and the inventory's DOM and style measurements. No screenshot (the
  pane's screenshot fails on this site).
