# Task contract — one form per part, sitewide

objective: >
  Issue #243: each part of site_v2 takes one form on every page. The picks in #243 note 4249336961
  are built as one sitewide change: seven text styles, one tab band, one segmented filter, one
  result chip, one competition group head, one row rhythm, one fact row, the block owning its
  vertical rhythm, start-aligned chart names, 4px and 8px corners, 1px table lines without stripes,
  one current-page form in the site header. Every value in system.css is in the fixed set of
  docs/design/design_standard.md. Approved pages keep their blocks, order and wording.

refs: >
  #243 note 4249336961 (the picks), decided by the coordinating agent under
  docs/design/design_standard.md, whose who-decides rule was approved in chat, 16 Nov 2026.

scope_paths:
  - .claude/task/243-one-form-per-part/
  - site_v2/src/styles/system.css
  - site_v2/src/components/*/*.astro
  - site_v2/src/layouts/Layout.astro
  - site_v2/src/lib/chartTheme.ts
  - site_v2/src/pages/[[]lang]/*.astro
  - site_v2/src/pages/[[]lang]/*/*.astro
  - site_v2/src/pages/[[]lang]/*/*/*.astro
  - site_v2/src/pages/[[]lang]/*/*/*/*.astro
  - docs/design/components.yml
  - docs/wireframes/block_standard.md
  - scripts/check_component_registry.py
  - tests/test_component_registry.py
  - tests/test_sentence_length_in_docs.py
  - tests/test_phone_built_pages_231.py
  - tests/test_phone_fixes_231.py
  - tests/fixtures/component_registry/baseline.json
  - tests/fixtures/design_inventory/baseline.json
  - tests/fixtures/design_inventory/baseline_quick.json
  - tests/fixtures/design_inventory/baseline_quick_fi.json
  - tests/fixtures/chart_screenshots/

protected_override: >
  docs/design/components.yml: the text sets, spacing set and part rules change to the picks of
  #243 note 4249336961, built in this file and system.css as that note says; visual details are
  the coordinating agent's under docs/design/design_standard.md, approved in chat, 16 Nov 2026.

impact_map: >
  writers: none; the stylesheet, page and component templates (markup only where a part's form
  needs it), the chart layout numbers, the component registry and its generated table. No dbt
  model, no export script, no data file.
  downstream: site_v2/dist only. leaf: consumption layer, no computation added or changed.
  layer_rules: not applicable; no computation.
  deploy_order: none; deploy:site-v2 is manual.
  blast_radius: the look of every page in every language: text sizes and weights, tab, filter,
  chip, group head, row, fact row, chart, crest, box and header forms. No block, order, wording
  or value changes. Registry and design-inventory pins only go down.

acceptance_criteria:
  - The parts page (scripts/parts_page.py against the local dev server) shows, for each kind, forms that differ only by first or last row in a list, by state (active and inactive, win, draw and loss) or by content (with or without a photo, a crest or a count); every remaining difference is named in acceptance_evidence.md.
  - Every font size, font weight, corner radius and spacing value in site_v2/src/styles/system.css is in the fixed set of docs/design/design_standard.md (sizes 11, 13, 15, 18, 20, 30 px; weights 400, 700; corners 4, 8 px; spacing 2, 4, 8, 12, 16, 24, 36, 48 px).
  - scripts/check_component_registry.py passes and no pin baseline (component registry, design inventory) rises.
  - On /teams/bayern-munchen/, /teams/germany/, a played match, a competition overview and the home page, at 375px and 1280px in EN, DE and FI, no rendered text contains "·" and no page scrolls sideways.
  - On those pages the same kind of thing takes the same form, and no unit is split and no line ends in an orphan word.
  - No block, block order, wording or value changes on any approved page.

approved_design:
  - home: #127
  - competitions: #128
  - competition: #129
  - matches: #130
  - match: #132
  - teams: #133
  - team: #134
  - players: #135
  - player: #136

depends_on:
  - none: the work is on main alone, after the separator dot change (!470) merged

shared_files:
  - tests/fixtures/component_registry/baseline.json
  - tests/fixtures/design_inventory/baseline.json
  - tests/fixtures/design_inventory/baseline_quick.json
  - tests/fixtures/design_inventory/baseline_quick_fi.json
  - tests/fixtures/chart_screenshots/

decisions_taken: >
  The picks of #243 note 4249336961, under docs/design/design_standard.md (fixed values, an
  existing form for every part, FotMob as the reference where the standard is silent). A pick that
  cannot be built as written is decided by that standard and reported to the coordinating session.
  No new mechanism, dependency or recurring cost.

decisions_reserved:
  - none: the picks are decided; any question goes to the coordinating session, and the CPO reviews the finished page group.

done_when:
  - python scripts/parts_page.py --base http://localhost:4325 before and after; distinct forms per kind reported.
  - python scripts/check_component_registry.py passes; baseline pins do not rise.
  - Full pytest and the site's node tests pass.
  - python scripts/ci_local.py --mr is green.

amendments: (none)
