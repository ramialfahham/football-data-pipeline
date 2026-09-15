# Rendered page evidence — `feat/149-competition-overview` (#149, the competition page's Overview tab built to #129)

Read from the RUNNING page (Astro dev server, `preview_start` name `v2`), on the committed sample
`competitions/BL1/2026.json` (the Bundesliga 2026/27 after three matchdays, produced by
`fetch_competition_payloads` against prod with the new warehouse objects inlined) and, for the
cup and the tournament, on `DFBP/2026.json` and `EURO/2024.json` placed locally (git-ignored).
Structure is the DOM; every value names what it was read from.

## 1. `/en/bundesliga/` at 700px — the four blocks in order

`document.title` → `Bundesliga: Overview`; `h1` → `Bundesliga`; `.tid .meta` →
`Germany · Season 2026 · Regular Season - 4` (the region label from `mart_competition_index`,
the served season year until #105, the provider's round text until #148).
`.comp-tabs .tab` → `Overview` (`<span class="tab on" aria-current="page">`), `Matchdays`,
`Teams`, `Players` — all four `SPAN`, none with an `href`.
`.eyebrow` in DOM order → `Table`, `Next matches`, `Deserved points`, `The season in numbers`.

## 2. The table

`.ctab-head` children → `#`, ``, `P`, `W`, `D`, `L`, `Goals`, `GD`, `Pts` (nine cells; the
empty one heads the crest-and-club column). First row → `<a class="ctab-row"
href="/en/teams/sc-freiburg/">`, text `1 SC Freiburg 3 3 0 0 10:1 +9 9`. `a.ctab-row` in the
Table section → 18, every one with an `/en/teams/{slug}/` href. Heading cells and row cells at the
same x positions: `[38, 70, 366, 403, 440, 476, 513, 576, 620]` for both (`alignedHead: true`).
`.wdl` cells all `display: block` at 700px.

At **375px** (mobile preset): heading and row cells again at identical x; the four `.wdl` cells
`display: none`; the longest name (`Borussia Mönchengladbach`) 35px tall = two lines, nothing
truncated; `document.documentElement.scrollWidth > innerWidth` → `false`.

## 3. Next matches

`a.fxrow[href]` → 9; first `/en/bundesliga/matches/2026-09-18-bayern-munchen-vs-1-fc-union-berlin/`.
`details.fxmore` → 0 (no fold). `.fxgroup .gh` → 0 (no competition heading — the h1 is the
competition).

## 4. Deserved points

`.bsub` → "Deserved points are the points a team's shot balance usually earns. …".
Board 1 `.bt` → `Better than the table says`, rows (`.nm` + `.pts`) → `1. FSV Mainz 05 -2.7`,
`1. FC Union Berlin -2.1`, `Bayer 04 Leverkusen -2.0`. Board 2 → `Worse than the table says`:
`Borussia Dortmund +2.7`, `FC Schalke 04 +2.0`, `SC Freiburg +1.8`. The Diff cell's computed
`font-weight` → `700`; Deserved and Pts cells carry `.n.num` without `.pts`. Each row an
`a.ctab-row` with an `/en/teams/{slug}/` href.

## 5. The season in numbers

`.frow` → 7, as `[tag, href, label, value, context]`:

| # | tag | href | label | value | context |
|---|---|---|---|---|---|
| 1 | DIV | — | Goals per match | 3.9 | 104 goals in 27 matches |
| 2 | DIV | — | Home wins | 14 of 27 | 5 draws, 8 away wins |
| 3 | DIV | — | Biggest margin | 0–5 | Hamburger SV vs 1. FSV Mainz 05, Regular Season - 2 |
| 4 | DIV | — | Most goals in a match | 3–4 | Borussia Mönchengladbach vs SV Elversberg, Regular Season - 2 |
| 5 | A | /en/teams/bayern-munchen/ | Longest unbeaten run | 3 matches | Bayern München, SC Freiburg, Borussia Dortmund, FC Augsburg |
| 6 | A | /en/teams/borussia-monchengladbach/ | Longest winless run | 3 matches | Borussia Mönchengladbach, Hamburger SV, 1. FC Union Berlin, SC Paderborn 07 |
| 7 | A | /en/bundesliga/matches/2026-09-19-eintracht-frankfurt-vs-sc-freiburg/ | The match that matters next | Eintracht Frankfurt vs SC Freiburg | 19 Sept, 13:30 |

Rows 3 and 4 do not link: a played match has no page. At 375px `.frow` computes one grid column
and `.fv` `text-align: left` (stacked).

## 6. German and Finnish

`/de/bundesliga/`: title `Bundesliga: Überblick`; meta `Germany · Saison 2026 · Regular Season - 4`;
tabs `Übersicht`, `Spieltage`, `Teams`, `Spieler`; sections `Tabelle`, `Nächste Spiele`,
`Verdiente Punkte`, `Die Saison in Zahlen`; headings `#`, ``, `Sp.`, `S`, `U`, `N`, `Tore`,
`Diff.`, `Pkt.`; goals `10:1`; first Diff `-2,7`; facts `Tore pro Spiel | 3,9 | 104 Tore in 27
Spielen`, `Heimsiege | 14 von 27 | 5 Unentschieden, 8 Auswärtssiege`, `Höchster Sieg | 0–5 |
Hamburger SV gegen 1. FSV Mainz 05, …`. `link[rel=alternate]` → `de`, `en`, `fi`, `x-default`
(→ `/en/bundesliga/`); canonical `https://matchdaypilot.com/de/bundesliga/`.
`/fi/bundesliga/`: title `Bundesliga: yleiskatsaus`; tabs `Yleiskatsaus`, `Kierrokset`,
`Joukkueet`, `Pelaajat`; sections `Sarjataulukko`, `Seuraavat ottelut`, `Ansaitut pisteet`,
`Kausi numeroina`; headings `O`, `V`, `T`, `H`, `Maalit`, `ME`, `P`; boards `Parempia kuin
taulukko kertoo`, `Heikompia kuin taulukko kertoo`.

## 7. A cup and a tournament — blocks absent where nothing is served

`/en/dfb-pokal/` (DFBP 2026, no standings, no deserved points): title `DFB-Pokal: Overview`;
meta `Germany · Season 2026 · Round of 32`; tabs `Overview`, `Rounds`, `Teams`, `Players`;
`.eyebrow` → `Next matches`, `The season in numbers` only; `a.fxrow` → 16; facts `Goals per
match | 4.6`, `Home wins | 2 of 32`, `Biggest margin | 0–11 | SC St. Tönis vs Eintracht
Frankfurt, Round of 64`, `Most goals in a match | 0–11 | …`; no run rows (the mart serves NULL
until a team has strung two matches together — the first render of this page showed a "run" of 1
held by all 36 clubs, which is what the rule now prevents).
`/en/euro/` (EURO 2024, finished): meta `Europe · Season 2024`; `.eyebrow` → `Table`, `The
season in numbers` only (no next matchday, no deserved points); `.ctab-section .gh .nm` → `Group
A` … `Group F` (six tables, the provider's "Ranking of third-placed teams" not rendered);
`a.ctab-row` → 24; facts `Goals per match | 2.3`, `Biggest margin | 5–1`, `Most goals in a match
| 5–1`, `Longest unbeaten run | 7 matches`, `Longest winless run | 4 matches`; no Home wins row
(null for national-team competitions).

## 8. Gates

`node --test` → 90 pass; `node scripts/check-page-specs.mjs` → 6 pages OK;
`python scripts/check_copy_gate.py` → OK, 606 strings, every `comp*` key in EN/DE/FI;
`python design-mocks/gen_competition_hub.py` + `check_competition_hub.py` → 10 checks pass
across the four kinds; `python -m pytest tests -q` → 1166 passed.
