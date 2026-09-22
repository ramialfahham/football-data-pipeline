# Acceptance evidence — #151, the Rankings tab and the Overview rework

Every item read from `site_v2/dist` built by `npm run build` on the committed sample (1,329 pages;
`audit-seo: 1330 built page(s) checked. OK.`; `check-built-pages: 849 match page(s) = 283
payload(s) x 3 ...; 3 fixtures page(s) and 3 rankings page(s) checked. OK.`), with a scratchpad
script (`evidence.py`) that strips Astro's `<!-- -->` splits and reads the elements' text, plus the
same script's headless-Chromium pass over the served `dist` at 375 and 700 px (`renders/`). Exit
codes read bare.

criteria_demonstrated:
  - THE BUILT RANKINGS PAGE EXISTS WITH THREE TABS, RANKINGS LIT, AND THE TWO BLOCK NAMES.
    `dist/en/bundesliga/rankings/index.html` (the address he ruled on the MR; the readings below were taken again on the renamed route and are unchanged): tabs `[('a','Overview'), ('a','Matchdays'), ('span','Rankings')]`
    (the span is `class="tab on"`), block names `['Team rankings', 'Player rankings']`;
    `dist/de/...`: `['Übersicht','Spieltage','Rankings']`, `['Team-Rankings', 'Spieler-Rankings']`;
    `dist/fi/...`: `['Yleiskatsaus','Kierrokset','Rankingit']`, `['Tiimirankingit', 'Pelaajarankingit']`.
    Exactly two `.sechead .eyebrow` per page.
  - EVERY BOARD HAS 1 TO 5 ROWS UNDER THE GROUP HEADINGS IN THE CATALOGUE'S ORDER; NO ZERO ON A
    DESC BOARD; NO BOARD STATES A DIRECTION. 24 boards per locale (the payload serves 24:
    12 team, 12 player — finishing has no qualifier after four matchdays), rows per board min 3
    max 5 (the two red-card boards hold 3: three sides on one red card, the zero rule cutting the
    rest); `.rkgroup > .gh .nm` reads `Goals · Shooting · Passing · One-on-one · Defending ·
    Discipline` for the team block and the same plus `Goalkeeping` for the player block, the
    order of `metric_groups.json` (DE `Tore · Schüsse · Pässe · Eins-gegen-eins · Defensive ·
    Disziplin (· Torwart)`, FI `Maalit · Laukaukset · Syötöt · Yksi vastaan yksi · Puolustus ·
    Kurinpito (· Maalivahti)`). Zero on a most-first board: `[]` in all three locales. The
    `.bnote` count is 0 on all three locales: no board says which way it ranks. The payload still
    serves the direction — its asc boards are exactly `['goals_against_per_match',
    'shots_on_goal_against_per_match']` — and the page reads as the CPO said it would without the
    note: EN "Goals against per match" tops at `0.5`, "Shots on goal against per match" at `2.0`
    (DE `Gegentore pro Spiel` `0,5`, FI `Maalilaukaukset vastaan ottelua kohden` `2,0`). Rows that
    are not links: 0.
  - THE OVERVIEW CARRIES EXACTLY THREE BLOCKS AND THE DESERVED TABLE IN THE SERVED RANK ORDER.
    `dist/en/bundesliga/index.html` `.sechead .eyebrow`: `['Table', 'Deserved points table', 'The
    season in numbers']` (DE `['Tabelle', 'Tabelle nach verdienten Punkten', 'Die Saison in
    Zahlen']`, FI `['Sarjataulukko', 'Ansaittujen pisteiden taulukko', 'Kausi numeroina']`); no
    "Next matches" / "Nächste Spiele" / "Seuraavat ottelut" on any of the three. `.ctab.dpt`: 18
    rows = the payload's 18 `deserved` rows, `.rk.num` reading `1, 2, 3, 4, 5, …` = the served
    `deserved_rank`; the head reads `# · (club) · Balance · Deserved · Pts · Diff` (DE `Bilanz ·
    Verdient · Pkt. · Diff.`, FI `Tase · Ansaitut · P · Ero`); the Deserved cell is the row's
    `.n.pts` (rendered 15px / 700 / rgb(59,176,114), the accent).
  - EVERY FACT ROW IS INERT ON EVERY COMPETITION PAGE. Swept every `dist/{de,en,fi}/<slug>/index.html`
    that is a competition page (144 of them): pages carrying an `a.frow` or the label "The match that
    matters next" / "Das nächste Spiel, das zählt" / "Seuraava avainottelu": `[]`. On the Bundesliga
    Overview: `a.frow` 0, `div.frow` 6, in all three locales.
  - THE MEASURED CHECK PASSES WITH THE RANKINGS PAGE LISTED. `docs/wireframes/block_standard.md`
    Pages table gains `Competition rankings | built | en/bundesliga/rankings/index.html`; `python
    scripts/check_design_inventory.py --dist site_v2/dist` → `20 pages · 2 viewports · 2
    languages · 80 renders · 0 failures · 0 warnings`, exit 0 (Home, the Overview, the Matchdays
    page and the Rankings page among the 20). `check_page_css.py`: 62 files, 0 findings.
  - THE MART SERVES rank_order ASC ON EXACTLY THE TWO "AGAINST" BOARDS. The branch's chain run
    inlined against prod (read-only, the !191 method; `team_mart_probe.sql`) for BL1 2026: 12
    distinct `metric_key`, `rank_order = 'asc'` on `goals_against_per_match` (top row Bayern /
    Dortmund at 0.5) and `shots_on_goal_against_per_match` (Bayern at 2.0), `desc` on the other
    ten; `cards_red` desc with three rows all at 1 and no zero row. In CI the same is held by
    `accepted_values` on `rank_order` and by `assert_mart_team_leaderboards_rank_follows_rank_order`
    (`data:build:mr`).
