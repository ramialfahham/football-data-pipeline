# Rendered page evidence — Finnish team compound

Method: the Browser pane drives the dev server (`preview_start` v2) on the Finnish Haaland page. Layout
was measured from text geometry through the accessibility-free route of `getClientRects` (the pane's
screenshot fails); no screenshot was taken. The local design check
(scripts/check_design_inventory.py) needs a built site, which `astro build` cannot produce at full
scale here, so it was not run; CI's validate:ui runs it on the MR (English and German, 280 and
1010px) and on main (every width and language).

Words on two lines, counted as `split` is in check_design_inventory.py. The intro paragraph was cloned
once per team name, with the old text (space, hyphen) and the new (no-break space, non-breaking
hyphen). The 31 names: Manchester City FC, Borussia Mönchengladbach, 1. FC Union Berlin, Bayer 04
Leverkusen, VfL Wolfsburg, Real Madrid, Atletico Madrid, Athletic Club, FC Barcelona, Paris Saint
Germain, Inter Milan, Sporting CP, Manchester United, Tottenham Hotspur, Newcastle United, West Ham
United, Eintracht Frankfurt, Hertha BSC, Real Sociedad, Aston Villa, FC Bayern München, RB Leipzig,
Borussia Dortmund, Werder Bremen, AC Milan, AS Roma, Crystal Palace, Nottingham Forest, Wolverhampton
Wanderers, Real Betis, Celta Vigo.

| width | words on two lines, before | after |
|------:|---:|---:|
| 280px | 2 | 0 |
| 320px | 17 | 0 |
| 360px | 19 | 0 |
| 375px | 14 | 0 |

The built intro paragraph and the legend (`.cmp-p .chart-legend`, "Muut Manchester City FC ‑pelaajat")
as they stand: 0 words on two lines and no horizontal overflow (scrollWidth within clientWidth) at 280
and 320px. The font has U+00A0 and U+2011 (cmap read with check-font-coverage.mjs's own reader).
