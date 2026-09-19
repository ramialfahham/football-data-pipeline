# Acceptance evidence — #150, the competition page's Matchdays tab

Every item read from `site_v2/dist` built by `npm run build` on the committed sample (283 fixture
payloads, `competitions/BL1/2026.json` with its 34 rounds), or from the dev server's rendered DOM,
exit codes read bare. The full-scale run (every unplayed match) is in `rendered_page_evidence.md`.

criteria_demonstrated:
  - THE THREE PAGES ARE EMITTED WITH THE OVERVIEW'S HEADER AND BAR. `dist/{en,de,fi}/bundesliga/fixtures/index.html`
    exist (check-built-pages: "3 fixtures page(s) checked"). The DOM at `/en/bundesliga/fixtures/`:
    crumbs `Home -> /en/` · `Competitions -> /en/competitions/` · `Bundesliga -> /en/bundesliga/` ·
    `Matchdays` (the `.here`); tabs `A:Overview -> /en/bundesliga/` · `SPAN:Matchdays [on]` ·
    `SPAN:Rankings`; header `h1` "Bundesliga", meta "Germany · Season 2026 · Regular Season - 4";
    no sentence under the bar (the first element after `nav.tabs` is the picker's `.md`). Titles:
    "Bundesliga: Fixtures and results 2026" / "Bundesliga: Spielplan und Ergebnisse 2026" /
    "Bundesliga: otteluohjelma ja tulokset 2026". DE crumb and tab "Spieltage", FI "Kierrokset".
  - EXACTLY ONE ROUND IS CHECKED AND IT IS THE FLAGGED ONE; THE ARROWS ARE THE NEIGHBOURS. DOM: 34
    `.md`, 34 `.md-in`, `checked: 1`, `openId: md-4`, `openTitle: "Matchday 4 Next"`; the open
    round's steps `LABEL.step prev for=md-3` and `LABEL.step next for=md-5`; round 1
    `SPAN.step prev off` + `LABEL.step next`, round 34 `LABEL.step prev` + `SPAN.step next off`;
    `visiblePickers: 1`, `visibleSections: 1`; clicking the prev label opens round 3 ("Matchday 3",
    one section visible). check-built-pages asserts the same on the built page and went RED with
    the `checked` attribute removed from the built HTML: "0 round(s) checked on load, expected 1".
  - THE PICKER LINE, THEN THE BLOCK; THE MEASURED CHECK PASSES EVERYWHERE. DOM: `.sechead` to the
    first `.dh` = 14px; `.mdstep` border-bottom 2px; `.step` 34×34; `.mdtitle .num` 13px 700
    uppercase; `.dh` 12px 700 uppercase. `python scripts/check_design_inventory.py --dist
    site_v2/dist --langs en,fi,de` → `19 pages · 2 viewports · 3 languages · 88 renders · 0
    failures · 0 warnings` with the new Pages row "Competition matchdays" (Expect: Block heading,
    Schedule block, Matchday picker, Tag, Date heading, Match row kick-off, Tab bar) and Home, the
    Overview and every mock still green; the same check went RED on the built page with no round
    checked ("Matchday picker · expected visible=1 · measured 0", "Schedule block · measured 0").
  - EVERY UNPLAYED ROW IS A LINK TO AN EMITTED PAGE. Round 4 DOM: 9 rows, 9 `a.fxrow`, hrefs
    `/en/bundesliga/matches/2026-09-18-bayern-munchen-vs-1-fc-union-berlin/`,
    `/en/bundesliga/matches/2026-09-19-eintracht-frankfurt-vs-sc-freiburg/`, …; `audit-seo:
    1195 built page(s) checked. OK.` (check 8, dead internal links, green with all 279 unplayed
    BL1 rows linked and their 279 payloads committed). Played rows, per the ruling: round 3 DOM
    `DIV.fxrow played` ×9, 0 links. check-built-pages asserts both on the REAL built page (the
    row's class matched in any attribute order; Astro emits `<a href="…" class="fxrow">`): with
    one unplayed `<a>` rewritten to a `<div class="fxrow">` in dist it prints "an unplayed row is
    not a link", exit 1; with one `<div class="fxrow played">` rewritten to a linked `<a>` it adds
    "a played row is a link, but no report page exists"; restored, OK.
  - SCORE ON PLAYED ROWS, WINNER BY WEIGHT; KICK-OFF WITH ZONE ON UNPLAYED; TBC ON A TBD FIXTURE.
    Round 3, row 1: "1. FC Union Berlin 1 | FC Schalke 04 3", `.g.num` weight 400 and
    `.g.num.winner` weight 700, both `color` ink/muted by class; a draw row: both `.g.num` 400;
    no `.when` on a played row. Round 4 row: `.when` = "18:30 / UTC" (`.t` 16px 700, `.rowtz`).
    TBD: with the first unplayed BL1 fixture's status set to TBD in a scratch copy of the payload
    the dev server rendered the time slot as "TBC UTC" / "Offen UTC" / "Avoin UTC" (en/de/fi);
    the payload was restored byte for byte (`cmp` identical) before the build.
  - THE TOP MATCH TAG ON THE FLAGGED ROW ONLY. DOM round 4: `topmatch: ["Eintracht Frankfurt |
    Top match"]`, one element; the page holds one `.topmatch` in total (`is_match_that_matters`
    true on fixture 1575168 only, `mart_next_matchday`'s flag). DE "Topspiel", FI "Huippuottelu".
  - CHECK-BUILT-PAGES COUNTS MATCH PAGES AGAINST THE PAYLOADS AND THE MANIFEST, AND GOES RED.
    Sample build: `849 match page(s) = 283 payload(s) x 3 (no manifest: sample build)`. Full-scale
    build: `15078 match page(s) = 5026 payload(s) x 3 = the warehouse's 5022 unplayed` (the +4 are
    the committed 2026-09-01 sample beside the export). RED once with one built match page moved
    out of dist: `match pages: 848 emitted, 849 expected (283 fixture payload(s) x 3 locales)`,
    exit 1; green again after restoring. Unit tests (`node --test`, 98 pass) pin the sampled-export
    case (`held 5022 … wrote 2`), the short-on-disk case and the manifest-without-count case.
  - EVERY NEW LABEL RESOLVES IN EN, DE AND FI. `python scripts/check_copy_gate.py` → `COPY GATE
    ok: 624 strings across 3 locales`; `check-page-specs: 7 page(s) validated`. The new keys, for
    the CPO's ruling on the MR: compSecSchedule "Schedule / Spielplan / Otteluohjelma",
    compPickerAria "Pick a matchday / Spieltag wählen / Valitse kierros", compNextTag "Next /
    Nächster / Seuraava", compTBC "TBC / Offen / Avoin", compTopMatch "Top match / Topspiel /
    Huippuottelu", seoCompetitionFixturesTitle and seoCompetitionFixturesDesc (the page title and
    description, three languages); the matchday title reuses compFactMatchday "Matchday {n} /
    Spieltag {n} / Kierros {n}".
