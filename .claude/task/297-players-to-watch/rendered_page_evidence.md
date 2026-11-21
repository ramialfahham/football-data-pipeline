# Rendered pages — #297, Players to watch

- **Instrument:** Playwright Chromium (the validate:ui image) on the built committed sample (`site_v2/dist` of the merged-result run), served locally; geometry read after the page loads. Page: `/en/bundesliga/matches/2026-11-20-bayern-munchen-vs-1-fc-koln/` and its DE and FI twins.
- **Boards:** two per page, in order Goals and assists then Ball actions per 90 (DE Scorerpunkte and Ballaktionen pro 90 Minuten, FI Tehopisteet and Pallotoiminnot per 90 minuuttia); each board's name sits 8px above its split.
- **280px (EN, DE, FI):** one column, no sideways scroll; each side's column head stands over its three player rows; the 12 rows per page are 248px wide and 59px high, none overflowing, in the name-over-position-and-value form ("photo name name / photo pos stat").
- **375px (EN):** one column, 343px rows, 56px high, no overflow; the value sits to the right of the name and position.
- **575px (EN):** one column, 543px rows; the split switches at 560px of the board's width, 592px of the page, because a board is its own container.
- **1010px (EN, DE, FI):** two columns; the two column heads on one line (same top) and the rows of the two sides level, 452px wide and 56px high.
- **Value alone:** every player row's value cell holds no letter at any width (no unit word); Ball actions per 90 reads one decimal, with the comma in DE and FI.
