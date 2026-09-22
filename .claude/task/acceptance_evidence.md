# Acceptance evidence — #152, metric groups defined in one place

Every item read from `site_v2/dist` built by `npm run build` on the committed sample (1,194 pages;
`audit-seo: 1195 built page(s) checked. OK.`; `check-built-pages: 849 match page(s) ... OK.`), with a
scratchpad script that strips Astro's `<!-- -->` splits and reads the heading elements' text
(`vs-group` spans on the team page, `mgroup` divs on the fixture page). Exit codes read bare.

criteria_demonstrated:
  - THE DE TEAM PAGE'S GROUP HEADINGS ARE THE GERMAN NAMES IN THE CATALOGUE'S ORDER.
    `dist/de/teams/manchester-united-fc/index.html` (team 33, the committed team sample):
    `['Tore', 'Schüsse', 'Pässe', 'Eins-gegen-eins', 'Defensive', 'Torwart', 'Standards']` — seven
    groups, the seven that have rows in the 16-row contract, in positions 1·2·3·4·5·7·8 of the
    ruled order (discipline, outcomes and playing_time hold no team row and are correctly absent).
    The EN page on the same payload reads `['Goals', 'Shooting', 'Passing', 'One-on-one',
    'Defending', 'Goalkeeping', 'Set pieces']`.
  - THE FI FIXTURE PAGE'S GROUP HEADINGS ARE THE FINNISH NAMES FROM THE #152 TABLE IN THE SAME
    ORDER. `dist/fi/bundesliga/matches/2026-09-18-bayern-munchen-vs-1-fc-union-berlin/index.html`
    (both windows populated, so the comparison renders twice): `['Maalit', 'Laukaukset', 'Syötöt',
    'Yksi vastaan yksi', 'Puolustus', 'Maalivahti', 'Erikoistilanteet']` per window; the same on
    `2026-09-19-borussia-monchengladbach-vs-1-fsv-mainz-05`.
  - NO DE OR FI PAGE CARRIES AN ENGLISH GROUP HEADING. All 796 `de/` and `fi/` pages under `dist`
    swept for the eleven English group names in the two heading elements: 0 found. Before this
    branch the same elements printed the raw `MetricGroup` string ("Goals", "Duels", …) on every
    locale (#98). `python scripts/check_design_inventory.py --dist site_v2/dist`: `19 pages · 2
    viewports · 2 languages · 76 renders · 0 failures · 0 warnings`, exit 0.
