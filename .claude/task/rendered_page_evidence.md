# Rendered page evidence — `feat/143-home-approved-design` (#143, Home built to #127)

Read from the RUNNING page (Astro dev server, `preview_start` name `v2`) with a fresh
`landing.json` exported on 2026-09-13 under the new round rule (31 competitions, 232 fixtures;
exported while the round selection still lived in the export SQL — the same SQL is now
`mart_next_matchday`, which does not exist in prod until the merge build, so the export cannot be
re-run against it yet; the read is a plain select, so the payload is the same),
and from the production build (`npm run build`) with the COMMITTED sample. The screenshot capture
in this pane crops the right third of the viewport, so geometry below is
`getBoundingClientRect()` / `getComputedStyle()` and structure is the DOM. Every value names
what it was read from so it can be re-read rather than trusted.

⚠ The committed sample (`site_v2/src/data/landing.json`, 4 fixtures, ≤2 per competition) cannot
show the fold, and it is NOT refreshed on this branch — a refresh is a set roll-forward
(`site_v2/src/data/README.md`) that would pin 232 fixture payloads. The fold evidence is from
the dev server with the fresh export placed in the same path and reverted before the commit
(`git checkout -- site_v2/src/data/landing.json`; `git status` clean on that path).

## 1. Dev server, `/en/`, fresh export — the fold

`document.querySelectorAll('.fxgroup').length` → **31**; `.fxrow` → **232**; `.fxrow[href]` →
**232** (every row links). Per group, rows outside `<details>`: max **3**. `details.fxmore` →
**18** groups (those with >3 fixtures); the 13 groups with ≤3 fixtures have no `<details>`.

First twelve groups, `{name, visible, summary, folded}`:
Eredivisie 3 "Show all 4" 1 · Ekstraklasa 3 "Show all 4" 1 · 2. Bundesliga 3 — 0 ·
Belgian Pro League 3 "Show all 4" 1 · La Liga 3 "Show all 5" 2 · Veikkausliiga 2 — 0 ·
Ligue 1 3 — 0 · Premier League 3 — 0 · Serie A 3 "Show all 6" 3 · Bundesliga 2 — 0 ·
Süper Lig 3 "Show all 4" 1 · Liga Portugal 3 "Show all 6" 3.

Opening Serie A's fold by clicking the summary: `details.open` → `true`; the three folded rows
(Como 1907–Parma, Torino FC–AS Roma, Inter Milan–Udinese Calcio) appear below "Show all 6" with
the divider between the summary and the first folded row and none under the last. Measured on a
4-row fold: `<details>` height **43.5px** closed → **124.2px** open; summary **43.5px** high,
`display:flex`, font **13px / 600**, `cursor: pointer`, `tabIndex 0`, receives focus
(`document.activeElement === summary` after `focus()`); chevron `transform` at rest
`matrix(0, 1, -1, 0, 0, 0)` (90°), `-90°` when `[open]`. A visible row is **80.7px** high.

## 2. Dev server, `/de/` and `/fi/` — the copy

Fetched and parsed: both **31** groups / **232** rows / **18** folds. Summary labels: DE
"Alle 4 anzeigen", FI "Näytä kaikki 4" (first three folds each). Source: `homeShowAll` in
`site_v2/src/i18n/strings.ts`, `{n}` interpolated by `t()`.

## 3. The order — unchanged, read from the headings

`.gh .nm` in document order: Eredivisie, Ekstraklasa, 2. Bundesliga, Belgian Pro League, La Liga,
Veikkausliiga, Ligue 1, Premier League, Serie A, Bundesliga, Süper Lig, Liga Portugal (Sunday
2026-09-13, Europe, then by kickoff/code), Liga Profesional de Fútbol (Argentina), Brasileirão
Série A, Major League Soccer (Sunday, CONMEBOL/CONCACAF), K League 1, J1 League, Saudi Pro League,
CAF Champions League (Sunday, AFC/CAF), Liga MX, AFC Champions League Elite (Monday), Coppa
Italia, FA Cup, Copa Libertadores (Tuesday), UEFA Europa League (Wednesday), UEFA Nations League
(24 Sep), Copa del Rey (26 Sep), UEFA Champions League (13 Oct), UEFA Conference League (15 Oct),
DFB-Pokal (27 Oct), AFC Asian Cup (7 Jan). `competitionOrder.mjs` is not in the diff.

## 4. No script added

Dev page `document.scripts`: 7 total, 3 inline — the header drawer (`SiteHeader.astro`) and
Astro's dev toolbar. Production `dist/en/index.html`: **2** `<script>` tags, the same count as
before this branch. The fold is `<details>`/`<summary>`.

## 5. Production build, committed sample

`npm run build` (prebuild: `node --test` + `check-page-specs.mjs`): **306 pages built**,
`audit-seo: 307 built page(s) checked. OK.` `dist/en/index.html`: 4 `.fxrow`, 0 `fxmore` (no
group exceeds 3 rows in the sample — the fold correctly does not render). Console on the dev
page after the fix: no errors (the two 500s in the log are from the intermediate build that
put JSX in Astro frontmatter, before `FixtureRow.astro` existed).

## 6. The mock

`python design-mocks/gen_home.py` → `home_mock.html` 112,217 bytes, 56 board rows, 19 fixtures;
`python design-mocks/check_home.py` → ALL PASS (14 checks, including the fold ones). With a
Browse section appended to the generated file the first two checks FAIL; restored, ALL PASS.
