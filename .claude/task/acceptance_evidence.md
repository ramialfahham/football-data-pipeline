# Verification — the component registry and the Inter font

Read on the committed sample build of `site_v2` (`npm run build`, 2,272 pages) in headless
Chromium, 2026-11-04. The same-machine main and branch tables are in `rendered_page_evidence.md`.

criteria_demonstrated:
  - One registry: `docs/design/components.yml` lists 38 components with their parts (class, text style or mark, breaks), wide form, narrow form and never-split units; it covers the 223 classes the built pages carry plus the two the fit script adds. `check_component_registry.py` generates the block standard's Elements table from it (143 rows, every earlier row's name and selector unchanged; the kick-off, Player row and Result row meta rows carry the approved changes) and fails a hand-edited table (RED: "the element table differs from the registry").
  - Inter: every built page preloads `/_astro/InterVariable.DiVDrmQJ.woff2` (352,240 bytes, SIL Open Font License 1.1, licence beside it); on the built Home page `.fx` computes `Inter, system-ui, …` and `document.fonts` reports `Inter 100 900 loaded`.
  - Font check: `check-font-coverage.mjs` reads 2,852 characters from the font and the visible text of all 2,272 built pages; it finds U+0084, U+0087 and U+008D (control characters in mangled player names), pinned at 3, 18 and 6; with no pins it fails "count rose · U+0084 · 3, baseline 0" (5 node tests pass).
  - Only registered classes: the measured check's class count falls on every page measured (EN, DE, FI at 280, 375, 700 and 1010px): Team page 60 → 30, match page 45 → 15, played match page 38 → 13, Competition overview 29 → 6, Home 23 → 6, Teams page 33 → 5, Matches page 31 → 7, Competitions index 26 → 5. The 35 classes a mock's CSS restyles stay out of the table, counted as `part gaps · mock-css 35`.
  - Text matches its set style: every generated row of a part with a text style asserts that style's size, weight and colour; the measured check finds no miss on any generated row on the eight page types above.
  - Stylesheet values: `check_component_registry.py` counts 8 font sizes no text style holds and 0 other values outside the sets; RED: a new 9.5px size, a 5.5px margin and a 650px query each raise a count.
  - Forms: the check counts 4 components that switch at a second width (crest, fact row, header, table); RED: a 650px query on `.lrow` raises `forms · list-row`.
  - Breaks: every part that never breaks and carries no gap is asserted on one line; the measured check finds no miss on those rows; 1 part is counted `lines-unmeasured` and 4 `style-varies`.
  - Protected: `docs/design/components.yml` is in the contract gate's protected files and routes to `cto-reviewer`; the hook tests deny its edit without `protected_override` and an `impact_map`.
  - Counts only fall: `tests/fixtures/component_registry/baseline.json` and `tests/fixtures/font_coverage/baseline.json` hold today's counts; a count off its pin fails in both directions, and a pin above main's fails `test_no_pin_rises_above_mains`. The design check's nine listed Inter rises are the one exception, approved in chat, 2026-11-04; `test_only_a_listed_rise_on_mains_old_value_is_allowed` proves a rise outside the list, and a listed rise on another main value, still fail.
  - Narrow rows: on all 1,746 match and Team pages, no result or player row runs past its box at 280, 320, 360, 375, 700 or 1010px in EN, DE and FI; main has 320 at 280px and none above. Goals and assists take two lines on 176 of 5,151 player rows at 280px, 2 at 320px and none from 360px. The dot after a result row's competition stays with its name: the built Team page carries `DFB-Pokal&nbsp;·` before the date.

`npm test` in `site_v2` passes in the build's prebuild. `pytest tests/test_check_component_registry.py
tests/test_governance_doc_parity.py tests/test_governance_hooks.py`: 432 pass, 3 skip. `check_page_css.py`:
0 findings, 0 counts off the baseline. Run alongside browser jobs, the governance hook tests that call git
through a subprocess fail on their 60-second timeout; alone they pass.
