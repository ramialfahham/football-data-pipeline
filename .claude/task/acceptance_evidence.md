# Verification — the match page's Show all metrics switch and team names

Checked locally on the branch: the six offline gates and `check_page_css.py`; the full pytest suite
(1,600 passed, 2 skipped); the site's node tests (132 passed). A copy of the branch built with
`npm run build` on the committed sample: exit 0, audit-seo checks 2,269 pages OK, check-built-pages
checks 1,644 match pages OK. The dev server was read in the browser on the local export of 18 Oct,
which predates the card totals, so its windows carry no card rows.

criteria_demonstrated:
  - Played match, Hoffenheim 2–3 Dortmund, Match stats: off shows 10 rows (Shots, Shots on target, Shots on target against, Passes, Pass accuracy, Possession, Duels, Duels won, Defensive actions, Fouls) under Shooting, Passing, One-on-one, Defending, Discipline; on shows all 28 in catalogue order and adds Goalkeeping and Set pieces. Upcoming Leverkusen vs Freiburg, Form comparison (DE): off 12 rows under six groups, on 31 rows under eight; Torwart and Standards hidden while off.
  - The label reads Show all metrics (EN), Alle Kennzahlen anzeigen (DE), Näytä kaikki tunnusluvut (FI); 13px, weight 600, ink-2; its right edge equals the comparison's at 375px (359px) and 1010px (950px), under the block explainer. Off by default; the track is sunk when off and ink-2 when on. No script. The accessibility tree reads `switch "Näytä kaikki tunnusluvut"`; Tab reaches it with a 2px accent focus ring, and Space turns it on.
  - The team names over both comparisons compute to 14px, weight 600, the ink colour.
  - block_standard.md lists Metric switch (`.tsw-lbl`) and Comparison team name (`.cmp .formhead .h`), and the Played match page expects both; `check_design_inventory.py` on the local build measured them with 0 failures and 0 warnings across 174 renders.
