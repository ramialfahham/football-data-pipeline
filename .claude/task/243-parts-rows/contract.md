# Task contract — parts library, the rows

objective: >
  Issue #243, the component-library step, first group: every row part of site_v2 exists once as an
  Astro component in site_v2/src/components/ui/, and every block that shows that row places the
  component instead of its own copy of the markup. Rows: list row, result row (result, meeting,
  goal and scorer forms), player row, competition row, fact row, table row and index row; the match
  row is already one component. Each row component sets its own link destination from the entity
  it shows. docs/design/components.yml maps each row part to its one component file, and
  scripts/check_component_registry.py fails markup of a registered part outside its component,
  under a pin that only goes down. No look change: a refactor of markup ownership, not a redesign.

refs: >
  #243 (component system), note 4249336961 (one form per part, merged as !471) and note 4253999647
  (the sitewide link rule). Visual details and engineering calls are the coordinating agent's under
  docs/design/design_standard.md.

scope_paths:
  - .claude/task/243-parts-rows/
  - site_v2/src/components/*/*.astro
  - site_v2/src/pages/[[]lang]/*.astro
  - site_v2/src/pages/[[]lang]/*/*.astro
  - site_v2/src/pages/[[]lang]/*/*/*.astro
  - site_v2/src/pages/[[]lang]/*/*/*/*.astro
  - docs/design/components.yml
  - docs/wireframes/block_standard.md
  - scripts/check_component_registry.py
  - scripts/parts_page.py
  - tests/test_check_component_registry.py
  - tests/test_parts_page.py
  - tests/test_phone_fixes_231.py
  - tests/fixtures/component_registry/baseline.json
  - tests/fixtures/design_inventory/baseline.json
  - tests/fixtures/design_inventory/baseline_quick.json
  - tests/fixtures/design_inventory/baseline_quick_fi.json

protected_override: >
  docs/design/components.yml: each row part's `file` becomes its one component file; a table-row,
  an index-row and a row-list component take the table's row parts, the competition list's row
  parts and the result and competition lists; each row component names the page type it links to
  (`links-to`); no text style, value, rule or measurement changes. The component-library step of
  #243 (each part built once as a component, every built page moved onto it with no change in
  look), approved in chat, 17 Nov 2026; links per the #243 link rule (issue #243 note 4253999647);
  visual details and engineering calls are the coordinating agent's under
  docs/design/design_standard.md, approved in chat, 16 Nov 2026.

impact_map: >
  writers: none; the component and page templates of site_v2 (markup moves into row components),
  the component registry, its generated table and its check. No dbt model, export script, data
  file or stylesheet rule.
  downstream: site_v2/dist only. leaf: consumption layer, no computation added or changed.
  guard: docs/design/components.yml is read by scripts/check_component_registry.py (the registry
  check and the block standard's generated table), scripts/check_design_inventory.py and
  scripts/design_inventory.py (the design check measures each part by its class and selector) and
  scripts/parts_page.py. Classes and selectors do not change, so what the design check measures
  does not change; only `file` and the component a part sits under change. A wrong `file` makes the
  new markup count rise and the check fail.
  layer_rules: not applicable; no computation.
  deploy_order: none; deploy:site-v2 is manual.
  blast_radius: none on what a visitor sees; the rendered HTML of every page stays the same, every
  difference listed in rendered_page_evidence.md with its reason. Registry and design-inventory
  pins only go down.

acceptance_criteria:
  - Every result, meeting, goal, scorer, player, competition, fact, table and index row on the built site is drawn by its one component in site_v2/src/components/ui/, and no other .astro file writes the markup of those rows.
  - scripts/check_component_registry.py counts, per registered component, its classes written in an .astro file other than its one component file, and fails when a count rises above its pin; every row component counts 0 except the two listed in acceptance_evidence.md with their reason.
  - scripts/check_component_registry.py fails a component whose `links-to` page types differ from the links its file builds.
  - The parts page (scripts/parts_page.py against the local dev server), before and after, shows for every part the same number of forms or fewer, and no new form.
  - On Home, Matches, Competitions, Teams, Players, the Bundesliga overview, matches and stats pages, /teams/bayern-munchen/, /teams/germany/, a played match, an upcoming match and a player page, at 375px and 1280px in EN, DE and FI, every tab, the rendered page is pixel-identical before and after, except where two copies of one part differed before and now take one form; every pixel and DOM difference is listed with its reason in rendered_page_evidence.md.
  - Every row links to the same page as before: a match row and a result row to the match page, a player row to the player page, a competition row to the competition page, a table row and a team index row to the team page.
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
  - none: the work is on main alone, after !471 merged

shared_files:
  - tests/fixtures/component_registry/baseline.json
  - tests/fixtures/design_inventory/baseline.json
  - tests/fixtures/design_inventory/baseline_quick.json
  - tests/fixtures/design_inventory/baseline_quick_fi.json

decisions_taken: >
  The library lives in site_v2/src/components/ui/, beside the match row, crest, block heading and
  fold it already holds. A row component takes the entity it shows and builds its own link; a
  block passes data, never a destination. A table row that leads nowhere is a div, like every other
  row that leads nowhere. Decided by the coordinating agent under docs/design/design_standard.md.
  No new mechanism, dependency or recurring cost.

decisions_reserved:
  - none: no look, wording or block changes; any question goes to the coordinating session.

done_when:
  - python scripts/parts_page.py --base http://localhost:4327 before and after; forms per part equal or fewer.
  - The before/after capture of the pages in acceptance_criteria reports pixel-identical screenshots; DOM differences listed.
  - python scripts/check_component_registry.py passes; baseline pins do not rise.
  - Full pytest and the site's node tests pass.
  - python scripts/ci_local.py --mr --full-scope is green.

amendments: (none)
