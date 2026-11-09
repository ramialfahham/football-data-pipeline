# Task contract — no word breaks at its hyphen, and the design check opens every tab

objective: >
  Issue #249. Across the site a word joined by a hyphen breaks at the hyphen on a narrow screen:
  "Saint-" at a line's end and "Germain" on the next, in team, player, competition, venue and region
  names and in prose. One build step keeps each such word whole: every letter-hyphen-letter word in
  a page's body text is wrapped in the registered no-break span (`.nb`), so the text a reader copies,
  searches and a search engine indexes keeps its real hyphen. A Top-match row takes its one-line
  form only while each name's longest word fits its space, as a table does. The design check opens
  every tab of every page's Tab bar and counts a defect shared by tabs once, so a gap on a tab that
  does not open first is measured; a page that shows a Tab bar with no tab to open fails. The
  registry's Unbreakable unit states the build step. The Player page (#259) follows with no gap.

refs: >
  #249, route approved in chat 2026-11-07. Every-tab check: parked/266-every-tab-check, approved in
  chat 2026-11-07.

scope_paths:
  - site_v2/src/middleware.ts
  - site_v2/src/lib/wholeWords.mjs
  - site_v2/src/lib/wholeWords.test.mjs
  - site_v2/src/lib/fitBlocks.mjs
  - site_v2/src/lib/fitBlocks.test.mjs
  - site_v2/src/styles/system.css
  - docs/design/components.yml
  - docs/wireframes/block_standard.md
  - scripts/check_design_inventory.py
  - tests/test_design_inventory.py
  - tests/fixtures/design_inventory/*
  - tests/fixtures/component_registry/*
  - tests/fixtures/chart_screenshots/*
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md

protected_override: >
  scripts/check_design_inventory.py and tests/test_design_inventory.py: the check opens every tab of
  a page (TABS_JS, OPEN_TAB_JS), counts a node, box or pair shared by tabs once, and judges a page's
  rules across its tabs (finish_page); two tests and the fixture counts_tabs.html pin it. Approved
  in chat, 2026-11-07, to land with #249. site_v2/src/middleware.ts is a new build mechanism, the
  route approved in chat, 2026-11-07. docs/design/components.yml, the Unbreakable unit only: its
  files, used-on and wide text name the build step, and never-split gains a hyphen-joined word;
  block_standard.md is regenerated from it.

impact_map: >
  writers: none in the warehouse.
  lineage: no dbt model changes, so no lineage moves.
  consumption: every built page passes the middleware; only text between tags inside `<body>`
  changes, never `<head>`, attributes, script, style, SVG, select, option, textarea or template.
  fitBlocks.mjs's `tagged` measure serves the Top-match row on Home, the Competition overview and
  the Team page. The Player row's gap (system.css) serves Players to watch on the match page, the
  line-ups and the Team page's squad. The design check's counts feed both design baselines.
  ci_layer_rules: scripts/check_design_inventory.py, scripts/check_page_css.py,
  scripts/check_component_registry.py, site_v2/scripts/check-built-pages.mjs,
  site_v2/scripts/check-font-coverage.mjs, site_v2/scripts/audit-seo.mjs.
  deploy_order: after !394, before the Player page (#259). One merge.
  blast_radius: every page's body text: a hyphen-joined word moves whole to the next line instead
  of breaking after its hyphen; the visible text, the copied text and the indexed text are
  unchanged. A Top-match row whose name has a word wider than its space takes the two-line form,
  the tag above. The Player row's gaps take the Result row's value, clamp(8px, 3cqw, 20px), in
  place of a fixed 12px: 8px on the narrowest rows, so a long hyphen-joined name keeps the numbers
  inside the row, and 13px in the widest. Both design baselines
  fall for the pages with hyphen breaks today.
  ci_cost: the design check in validate:ui opens every tab: +36 s on a merge request (227 → 263 s)
  and +76 s on main (665 → 741 s), measured on one build; accepted in chat, 2026-11-08.

approved_design:
  - home: #127
  - competitions: #128
  - competition: #129
  - matches: #130
  - match: #132
  - teams: #133
  - team: #134
  - player: #136

decisions_taken: >
  The registry is the standard; "Name in whole words" already says a name wraps only between words,
  and a hyphen-joined word counts as one word, so no new rule; the Unbreakable unit names the build
  step that applies it. The no-break span, not the non-breaking hyphen character, so copy, find and
  search keep the real hyphen (both approved in chat, 2026-11-07). A tab is a tab of the registered
  Tab bar; the matchday picker is not a Tab bar.

decisions_reserved: none.

done_when:
  - python -m pytest tests passes.
  - npm test, npm run build and its audits pass in site_v2.
  - The design check opening every tab reports no pin above main's on any page.

acceptance_criteria:
  - "No letter-hyphen-letter word breaks at its hyphen on any built page, in any tab, at 280, 320, 360, 375, 700 and 1010px in EN, DE and FI."
  - "The copied and indexed text keeps the real hyphen: the page's text content is unchanged by the build step."
  - "A Top-match row takes its one-line form only while every name's longest word fits its space."
  - "The design check opens every tab of every page and counts a defect shared by tabs once."
  - "No design pin rises above main's; the pins that fall are lowered from CI's measurement."

amendments: (none)
