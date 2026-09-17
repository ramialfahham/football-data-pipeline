# Acceptance evidence — #153, items 1–3: the element inventory, one stylesheet, the lint, the measured check

Every item read from a built site (`astro build` on the committed sample, the two untracked export
payloads parked outside the tree) or from a fresh render of the generators, by the check itself
or by a script beside it; the numbers are in `rendered_page_evidence.md`.

criteria_demonstrated:
  - THE MEASURED CHECK IS GREEN ON EVERY LISTED PAGE. `python scripts/check_design_inventory.py
    --langs en,fi,de` (the built site at `site_v2/dist`, every mock generator rendered fresh):
    `18 pages · 2 viewports · 3 languages · 82 renders · 0 failures · 0 warnings`, exit 0 — the
    5 built page types in EN/FI/DE and the 13 mock pages in EN/FI (a mock has no DE), at 375 and
    700. The same command with `--langs en,fi` (the inventory's own languages): `18 pages · 2
    viewports · 2 languages · 72 renders · 0 failures`.
  - THE LINT IS GREEN ON THE TREE AND RED ON THE TREE BEFORE IT. `python scripts/check_page_css.py`:
    `page-css lint: 57 files scanned, 0 finding(s)`, exit 0. Run against the base commit's
    `site_v2/src` and `design-mocks` (exported with `git archive HEAD`): `57 files scanned, 128
    findings` — `Masthead.astro:25 · style= on <div> · eyebrow` (1), `rows.py` (11),
    `interaction.py` (15), `gen_competition_matchdays.py` (17), `gen_competition_teams.py` (20),
    `gen_overview_after_teams.py` (12), `gen_home_with_rules.py` (15), `gen_top_players.py` (16),
    `gen_top_teams.py` (16), `gen_matches.py` (3), `gen_block_standard.py` (2).
  - THE RED PROOF. `python -m pytest tests/test_design_inventory.py -q`: `31 passed` (Chromium
    installed here, so the three browser tests ran). `red.html` fails on exactly `Block heading`
    (measured 11px), `Block heading gap` (measured 34.0px), `Row link` (hover and press measured
    `rgb(22, 25, 32)`, the surface), `Table row` (row 1 measured the tint; border 1px),
    `Tab bar` (`scrollWidth 376 > clientWidth 343`) and `Fact row value` (14px/600/ink);
    `green.html` passes with `0 failures`, every exercised row matched.
  - THE BUILT OVERVIEW SHOWS THREE TABS AND THE BAR FITS IN THREE LANGUAGES. `dist/en/bundesliga/`:
    `nav.tabs.comp-tabs` → `Overview` (`span.tab.on[aria-current=page]`), `Matchdays`, `Rankings`;
    `/de/`: `Übersicht`, `Spieltage`, `Rankings`; `/fi/`: `Yleiskatsaus`, `Kierrokset`,
    `Rankingit`. The check's `Tab bar · fits` and `Tab · one-line` pass for `Competition overview`
    at 375 and 700 in en, fi and de (part of the 82-render run above; the DE run is what the
    `--langs en,fi,de` invocation adds).
  - THE FOUR GENERATORS OF RECORD RE-RENDER TO THE SAME MARKUP. Everything outside `<style>`:
    `competition-rankings` identical, `home` identical, `competition-overview` differs in one line
    (the `<title>`, which lost its date on !195), `competition-matchdays` differs only by the
    picker nesting — with each matchday's `.md` wrapper, radio and `nav.mdnav` normalised away
    and `section.md[data-md]` read as `section`, the residual diff is 0 lines over 538; 34 steps
    and 34 titles identical in order, 34 radios, matchday 4 checked in both. The nested picker
    switches by the arrow labels (4 → 5 → 4 → 3) and by ArrowRight on the checked radio (3 → 4),
    one step visible at every point. All four fresh renders measure green (above).
  - THE INVENTORY DOCUMENT. `docs/wireframes/block_standard.md` carries 40 element rows (every
    element of the approved plan's table, two of them split into the competition group head and
    the metric group heading per the ruling "Home with line, Rankings without") with selector,
    rule, `Measured as`, status and where ruled, and 18 page rows; `python
    scripts/design_inventory.py --count` → `40 elements, 95 assertions, 18 pages`;
    `docs/wireframes/00_overview.md`'s owner table gains the row "What is an ELEMENT …" pointing
    at it. `grep -c "Measured as" docs/wireframes/block_standard.md` → 3, not the 1 the criterion
    wrote: the table header plus the two sentences of the reading guide that name the column;
    the criterion's intent — one table with that column, parsed — holds and is what the parser
    enforces (`ELEMENT_COLUMNS`, a renamed column is exit 2).
  - NO PAGE CSS. `grep -rn "<style" site_v2/src` prints nothing; `grep -rn 'style=' site_v2/src
    --include=*.astro` finds only the data-driven bar widths on `.w/.d/.l`, `.fill` and
    `.vs-fill` (no inventory class); the lint's own output above is 0 findings.
