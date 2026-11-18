# Task contract — the last page-local copies of library parts

objective: >
  Issue #243, step 4's check: the registry counts three pieces of markup outside the part they
  copy. The Team page's Deserved points table writes its own table rows; it moves onto the table
  row component, and the table row's second line under the name becomes one form for every
  table: 13px muted at line height 1.2, the ranking tables' form. That moves
  the Deserved table's second line from line height 1.25 to 1.2, the one intended look change.
  The match header's status word ("Match preview", or how a played match ended) writes the block
  heading's `eyebrow`, and the line-up column head writes the player row's `ps` for a team's
  formation; each becomes a part of the component that draws it (the match header, the two-column
  head), with the same computed style, no look change.

refs: >
  #243 (component system), note 4249336961 (one form per part). Visual details and engineering
  calls are the coordinating agent's under docs/design/design_standard.md.

scope_paths:
  - .claude/task/243-page-copies-to-parts/
  - site_v2/src/components/fixture/Masthead.astro
  - site_v2/src/components/fixture/MatchLineups.astro
  - site_v2/src/components/team/TeamDeserved.astro
  - site_v2/src/styles/system.css
  - docs/design/components.yml
  - docs/wireframes/block_standard.md
  - scripts/parts_page.py
  - tests/fixtures/component_registry/baseline.json
  - tests/fixtures/chart_screenshots/*
  - tests/fixtures/design_inventory/baseline.json
  - tests/fixtures/design_inventory/baseline_quick.json
  - tests/fixtures/design_inventory/baseline_quick_fi.json

protected_override: >
  docs/design/components.yml: the match header gains its status-word part, the two-column head
  gains its formation part, the Deserved points table's own sub-line part goes, its rows now
  being the table row's, and the sub-line part moves from the board to the table row as the
  second line of every table (selector `.ctab .tm .sub`, the elements the stylesheet's
  `.ctab .tm .ent .sub` styles) with a rule naming any table's second line, the board keeping a
  part without text for its narrow rules (`.board .ent .sub`); its text style and measurement do
  not change, and no other part, text style, value, rule or measurement changes. The
  component-library step of #243 (each part built once as a component, every built page moved
  onto it), approved in chat, 17 Nov 2026; visual details and engineering calls are the
  coordinating agent's under docs/design/design_standard.md, approved in chat, 16 Nov 2026.

impact_map: >
  writers: none; two match-page components and the Team page's Deserved points component, the
  selectors in system.css that style them, the component registry, its generated table and its
  pins. No dbt model, export script, data file or test logic.
  downstream: site_v2/dist only: every match page and every Team page's Performance tab. leaf:
  consumption layer, no computation.
  guard: docs/design/components.yml is read by scripts/check_component_registry.py (the registry
  check and the block standard's generated table), scripts/check_design_inventory.py and
  scripts/design_inventory.py (the design check measures each part by its class and selector),
  scripts/parts_page.py and site_v2/scripts/check-term-list.test.mjs. Two parts are added with the
  selectors the markup now carries and one gap-only part goes with its class; no measured class or
  selector changes. A wrong class makes the markup count rise and the check fail.
  layer_rules: not applicable; no computation.
  deploy_order: none; deploy:site-v2 is manual.
  blast_radius: the Deserved points table's second line ("per match" under a column's name) on
  every Team page's Performance tab, line height 16.25px to 15.6px; nothing else a visitor sees.
  Every match page and the Team pages are captured before and after.

acceptance_criteria:
  - scripts/check_component_registry.py counts 0 markup outside the block, player-row and table-row components, and tests/fixtures/component_registry/baseline.json pins all three at 0.
  - Every match page of the local data at 375px and 1280px (EN; DE and FI for every played match and one upcoming match) renders pixel-identical before and after, with the same href list and visible text.
  - Every Team page of the local data at 375px and 1280px in EN, DE and FI renders pixel-identical before and after except the Deserved points table, whose second lines are 13px muted at line height 1.2; the same href list and visible text; every difference is listed with its reason in rendered_page_evidence.md.
  - No block, wording, value or link changes on any page.

approved_design:
  - match: #132
  - team: #134

depends_on:
  - none: the work is on main alone

shared_files:
  - tests/fixtures/component_registry/baseline.json
  - docs/design/components.yml
  - site_v2/src/styles/system.css

decisions_taken: >
  The status word and the formation keep their text style under a class of their own component;
  the stylesheet gives the status word the block heading's declaration through one selector list,
  so the two keep one form. The table row's second line takes one form for every table, 13px
  muted at line height 1.2 (the ranking tables'), and the Deserved points table takes it.
  Decided by the coordinating agent under docs/design/design_standard.md. No new mechanism,
  dependency or recurring cost.

decisions_reserved:
  - none: any question goes to the coordinating session.

done_when:
  - The before/after capture of every match page and every Team page reports pixel-identical screenshots, the same hrefs and the same text, except the Deserved table's second line; every difference listed.
  - python scripts/check_component_registry.py passes; baseline pins do not rise.
  - Full pytest and the site's node tests pass.
  - python scripts/ci_local.py --mr is green.

amendments: >
  The Deserved points table moves onto the table row in this task, its second line at the table
  row's 1.2 line height, table-wide: the coordinating agent's form pick under
  docs/design/design_standard.md (mandate approved in chat, 16 Nov 2026), 18 Nov 2026.
  scripts/parts_page.py names the Deserved table's sub-line part in its Meta line kind; that part
  goes, so its name leaves the kind's list (the coordinating agent's engineering call, same
  mandate), 18 Nov 2026.
  The sub-line part moves from the board to the table row in docs/design/components.yml, so the
  registry measures the second line of every table the stylesheet styles (review round 1); the
  design inventory's Pages table in docs/wireframes/block_standard.md and the parts page's Meta
  line kind follow the part's new name; same mandate, 18 Nov 2026.
  The Team page's chart screenshot pins (tests/fixtures/chart_screenshots/, the scatter and strip
  plots below the Deserved table) are retaken on Linux by the design check: the charts sit up to
  1px higher at a fractional offset, so their text rasterises a pixel apart; nothing in a chart
  changes; same mandate, 18 Nov 2026.
