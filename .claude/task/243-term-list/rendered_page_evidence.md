# Rendered page — the league table's Points column

Measured in the browser on the dev server, `/{lang}/bundesliga/`, the standings table's last head
cell (scrollWidth / clientWidth, its right edge against the table's right edge).

| Width | EN "Points" | DE "Punkte" | FI "Pisteet" | Page overflow |
|---|---|---|---|---|
| 280px | 48/48, right 264.0 = table 264.0 | 48/48, right 264.0 = table 264.0 | 48/48, right 264.0 = table 264.0 | 0 |
| 375px | 48/48, right 359.0 = table 359.0 | 48/48, right 359.0 = table 359.0 | 48/48, right 359.0 = table 359.0 | 0 |
| 1010px | 48/48, right 949.5 = table 949.5 | 48/48, right 949.5 = table 949.5 | 48/48, right 949.5 = table 949.5 | 0 |

No team name in the table overflows its cell at 375 or 1010px.

Design check (`scripts/check_design_inventory.py`, 280 and 1010px, EN and DE, quick baseline): the
same failures as plain main at the same commit, none added.
