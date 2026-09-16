# Acceptance evidence — competition page, Overview tab: build the approved design (#149)

Every item read from the running page (Astro dev server) on the committed sample; the numbers and
selectors are in `rendered_page_evidence.md`.

criteria_demonstrated:
  - THE PAGE RENDERS THE HEADER, THE TAB BAR AND THE FOUR BLOCKS IN ORDER, IN THREE LOCALES.
    `/en/bundesliga/`: h1 `Bundesliga`, meta `Germany · Season 2026 · Regular Season - 4` (crest
    rendered from the served `logo_url`), tabs `Overview` (`span.tab.on[aria-current=page]`),
    `Matchdays`, `Teams`, `Players` — four `SPAN`s, none with an href; `.eyebrow` in DOM order
    `Table`, `Next matches`, `Deserved points`, `The season in numbers`. `/de/bundesliga/`:
    `Tabelle`, `Nächste Spiele`, `Verdiente Punkte`, `Die Saison in Zahlen`; `/fi/bundesliga/`:
    `Sarjataulukko`, `Seuraavat ottelut`, `Ansaitut pisteet`, `Kausi numeroina`.
  - THE TABLE. Heading cells `#`, ``, `P`, `W`, `D`, `L`, `Goals`, `GD`, `Pts`; Freiburg's row
    `1 SC Freiburg 3 3 0 0 10:1 +9 9` as `<a class="ctab-row" href="/en/teams/sc-freiburg/">`;
    18 such rows, every href `/en/teams/{slug}/`. At 375px the four `.wdl` cells compute
    `display: none` and heading and row cells sit at identical x (`alignedHead: true` at both
    375px and 700px).
  - NEXT MATCHES. `a.fxrow[href]` → 9, the payload's whole next matchday, first href
    `/en/bundesliga/matches/2026-09-18-bayern-munchen-vs-1-fc-union-berlin/`; no `details.fxmore`
    (no fold) and no `.fxgroup .gh` (no competition heading).
  - DESERVED POINTS. The explanation paragraph (`.bsub`), then `Better than the table says` with
    `1. FSV Mainz 05 -2.7`, `1. FC Union Berlin -2.1`, `Bayer 04 Leverkusen -2.0` (the served
    `deserved_points_gap_rank` 1, 2, 3 — the warehouse's order; the gap keeps the catalogue's
    actual-minus-deserved sign) and `Worse than
    the table says` with `Borussia Dortmund +2.7`, `FC Schalke 04 +2.0`, `SC Freiburg +1.8`; the
    Diff cell computes `font-weight: 700`, the other two numbers are plain.
  - THE SEASON IN NUMBERS. Seven `.frow`s, each label · value · context: `Goals per match | 3.9 |
    104 goals in 27 matches`; `Biggest margin | 0–5 | Hamburger SV vs 1. FSV Mainz 05, Regular
    Season - 2` — the earliest 5–0 of the season, which is what the tie rule ruled on #129 picks
    (the Freiburg 5–0 of Matchday 3 came later); the two match facts are `DIV`s without an href,
    because a played match has no page on this site (the criterion as first drafted said they
    link — corrected in the contract with that ruling as the authority); the two run facts and
    the match that matters are `A`s (`/en/teams/bayern-munchen/`, `/en/teams/borussia-
    monchengladbach/`, `/en/bundesliga/matches/2026-09-19-eintracht-frankfurt-vs-sc-freiburg/`).
    No `.frow` for a null fact: the cup page renders no run rows while its runs are null.
  - BLOCKS ABSENT WHERE NOTHING IS SERVED. `/en/dfb-pokal/` (no standings, no deserved points):
    `.eyebrow` → `Next matches`, `The season in numbers` only, tabs read `Rounds`. `/en/euro/`
    (finished, national teams): `.eyebrow` → `Table`, `The season in numbers` only; six group
    tables `Group A`…`Group F` and no ranking table; no Home wins row.
  - `cd site_v2 && npm test` → 90 pass (7 new in `competitionPayload.test.mjs`);
    `node scripts/check-page-specs.mjs` → `6 page(s) validated … OK`; the competition spec has no
    `stub` key and lists `mart_competition_index`, `mart_standings`, `mart_next_matchday`,
    `mart_team_profile`, `mart_competition_season_summary`; `STUB_PAGES` holds only the player
    page.
  - `python scripts/check_copy_gate.py` → `COPY GATE ok: 606 strings across 3 locales …`, every
    new `comp*` key present in EN, DE and FI.
