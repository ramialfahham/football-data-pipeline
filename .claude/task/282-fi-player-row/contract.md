# Task contract — Finnish player rows fit at 280px

objective: >
  Issue #282. A player row under 280px puts the player's name on its own line and the position
  and the numbers on the second, so a long name next to the Finnish "maalisyöttöä" no longer
  pushes the row out at 280px, and main's full design check passes again.

refs: >
  #282, approved in chat, 2026-11-10, with the player row's registry rule.

scope_paths:
  - .claude/task/282-fi-player-row/
  - site_v2/src/styles/system.css
  - docs/design/components.yml
  - docs/wireframes/block_standard.md
  - tests/fixtures/component_registry/baseline.json
  - tests/test_check_component_registry.py
  - tests/test_design_inventory.py
  - tests/fixtures/design_inventory/baseline.json

protected_override: >
  docs/design/components.yml: the player row's rule gains the under-280px clause, with the exact
  text approved in chat, 2026-11-10. The switch set gains w280 and the player row its narrow form
  below w280, also approved in chat, 2026-11-10. tests/test_design_inventory.py: its no-rise test
  lets a width_rules pin rise for a width the registry's switch set declares, approved in chat,
  2026-11-10. tests/test_check_component_registry.py: its no-rise test lets the switch set's size
  rise, approved in chat, 2026-11-10.

impact_map: >
  writers: none in the warehouse.
  lineage: no dbt model and no export change, so no lineage moves.
  consumption: system.css's .plrow rules style every player row: PlayerRow.astro (Match page
  Players to watch), MatchLineups.astro (Match page line-ups) and TeamSquad.astro (Team page
  squad). The new rule is a container query on the row's .lrow, so it fires only where that row is
  under 280px. Measured on this branch's build across 548 Match pages and 34 Team pages per
  language: a player row is under 280px at viewports below about 312px (248px at 280, 268px at
  300, 278px at 310) and in the Match page's two-column lists from 560px to about 640px (243px at
  560, 279px at 640); there every row takes the narrow form, and at 320, 360, 375, 700 and 1010px
  no row does.
  guard: docs/design/components.yml is read by scripts/check_component_registry.py, which
  regenerates the block standard's Elements table from it, and by
  scripts/check_design_inventory.py through that table. The player row's rule text changes, the
  switch set gains w280, and the player row declares its narrow form below it; its class, selector
  and "fits" measurement stay, so no design assertion changes. check_component_registry.py counts
  a switch width no set holds and a component switching at an undeclared width; both stay at 0,
  and its pinned switch set size in tests/fixtures/component_registry/baseline.json moves from 12
  to 13. If the text and the table disagree, check_component_registry.py fails the build.
  The two no-rise tests (test_no_pin_rises_above_mains in tests/test_check_component_registry.py
  and in tests/test_design_inventory.py) run in test:python and locally. The registry's test stops
  counting the switch set's size only, which its check already pins in both directions; the other
  set sizes and every gap count keep their no-rise rule, and a unit test pins that. The inventory's
  test drops from its rises only a static width_rules key equal to a declared switch width, or to
  it less 0.02px as a max-width query writes it, so an undeclared width, a near one included,
  still fails, and every other count keeps its rule. scripts/design_inventory.py, whose rises() the rest of the machinery
  calls, is unchanged. tests/fixtures/design_inventory/baseline.json's static width_rules gains
  "279.98px": 1, which check_page_css.py compares in both directions.
  ci_layer_rules: scripts/check_component_registry.py, scripts/check_page_css.py,
  scripts/check_design_inventory.py.
  deploy_order: one merge.
  blast_radius: every player row under 280px takes the two-line form: on Match and Team pages
  below about 312px, and in the Match page's two-column lists from 560px to about 640px, where
  main's rows stick out today too (FI 6 and DE 3 at 560px, FI 3 at 600px). A row 280px or wider
  is unchanged. The design check's Match page counts return to main's baseline: miss · List row
  0, miss · Player row 0, scroll 2184.

acceptance_criteria:
  - At 280px wide, no player row on a Match page or a Team page sticks out of its row, in English, German or Finnish.
  - Where a player row is narrower than 280px, the player's name takes the whole first line, and the position shares the second line with the goals and assists, which stay on the right.
  - Where a player row is 280px or wider, it looks as it does today.

approved_design:
  - match: #132
  - team: #134

decisions_taken: >
  The narrow form follows the competition row's at 340px (name across the row, numbers to the
  second line), a small display rule settled by consistency. The Finnish word stays as the term
  list has it. The registry rule text and the acceptance criteria were approved in chat,
  2026-11-10. No new mechanism: one container query in system.css, as the stylesheet already
  uses.

decisions_reserved:
  - none: the rule text and the criteria are approved, and the layout reuses the competition row's narrow form.

done_when:
  - The offline gates pass, check_component_registry.py regenerates block_standard.md with no other change, and npm test passes.
  - The full design check on a local build, at 280,320,360,375,700,1010 and en,de,fi, gives Match page miss · List row 0, miss · Player row 0, scroll 2184, and no FAIL or COUNT line above main's baseline.

amendments:
  - 2026-11-10: + tests/fixtures/component_registry/baseline.json, and components.yml gains the
    switch width w280 and the player row's narrow form below it — authority: approved in chat,
    2026-11-10; content: the registry check refuses a width no switch set holds, and the switch
    set size pin moves from 12 to 13.
  - 2026-11-10: + tests/test_check_component_registry.py, tests/test_design_inventory.py and
    tests/fixtures/design_inventory/baseline.json — authority: approved in chat, 2026-11-10;
    content: the registry's no-rise test lets the switch set's size rise, the inventory's lets a
    width_rules pin rise for a width the switch set declares, and the page-CSS width pin gains
    279.98px at 1.
  - 2026-11-10: criterion 3 reads "Where a player row is 280px or wider, it looks as it does
    today." — authority: approved in chat, 2026-11-10; content: the narrow form also applies to
    rows under 280px at about 290–311px and to the Match page's two-column lists at about
    560–640px.
