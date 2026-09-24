# Rendered page evidence — `feat/address-words` (#158)

No markup, style or copy changes: every change is an `href`, a route parameter or an hreflang target.
What was rendered and measured to show that:

## 1. The measured design check on the built site

`npm run build` on the committed sample (1330 pages, exit 0), then `python
scripts/check_design_inventory.py --dist site_v2/dist` → `21 pages · 3 viewports · 3 languages
(pages per language: en 21, de 7, fi 21) · 147 renders · 0 failures · 21 warnings`, the warnings
all the known 700px header row (`.header-in` scrollWidth > clientWidth), none new. Widths 375, 700
and 1010px. The seven built rows open their German and Finnish files through the word table
(`resolve_built` → `translate_path`), so `de/bundesliga/statistiken/index.html` and
`fi/bundesliga/tilastot/index.html` are the files measured for "Competition rankings".

## 2. The built HTML

- `/de/bundesliga/index.html` tab bar: `Übersicht` (on) · `Spieltage` → `/de/bundesliga/spiele/` ·
  `Ranglisten` → `/de/bundesliga/statistiken/`; crumb and link `Wettbewerbe` → `/de/wettbewerbe/`.
- A script over all 1330 pages: 3987 reciprocal hreflang pairs, 0 problems; 0 paths at an old shape.

## 3. The dev server (`preview_start` v2)

Every same-shape route resolves (Astro 5.18.2 tries each matching route in turn): 200 with the right
h1 for `/de/wettbewerbe/`, `/fi/kilpailut/`, `/de/bundesliga/spiele/`, `/fi/bundesliga/ottelut/`,
`/de/bundesliga/statistiken/`, `/fi/bundesliga/tilastot/`, `/en/bundesliga/stats/`,
`/de/mannschaften/borussia-dortmund/`, `/fi/joukkueet/borussia-dortmund/`, `/de/spieler/p-schick-794/`,
`/fi/pelaajat/p-schick-794/` and a match under `/de/bundesliga/spiele/`; 404 for `/de/teams/x/` and
`/en/bundesliga/fixtures/`. Console: only those two deliberate 404s. The dev log carries a Vite
dependency-scan error on a comment inside `Layout.astro`, a file this change does not touch.
