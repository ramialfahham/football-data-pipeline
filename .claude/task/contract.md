# Task contract — Compared with last season follows the registry's table and group heading rules

objective: >
  Issue #263. The Team page's Compared with last season block follows the registry's Table and
  Metric group heading rules (`docs/design/components.yml`): each metric group's table has its own
  head row, rows striped from the second, names 14px semi-bold, 26px from the group heading to the
  table. The Player page (#259) reuses the block.

refs: >
  #263, approved in chat 2026-11-07. Design: #134.

scope_paths:
  - site_v2/src/components/team/TeamLastSeason.astro
  - site_v2/src/styles/system.css
  - docs/design/components.yml
  - docs/wireframes/block_standard.md
  - tests/fixtures/component_registry/*
  - tests/fixtures/design_inventory/*
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md

protected_override: >
  docs/design/components.yml, one line: the last-season table's `yoyt-head` part goes, because its
  class leaves the code; no rule changes (approved in chat, 2026-11-07).

impact_map: >
  writers: none in the warehouse.
  lineage: no dbt model changes, so no lineage moves.
  consumption: the Team page's Performance tab, block Compared with last season. The shared
  classes it changes (`.ctab.yoyt`) have no other reader on main.
  ci_layer_rules: scripts/check_page_css.py, scripts/check_design_inventory.py,
  scripts/check_component_registry.py.
  deploy_order: before the Player page (#259). One merge.
  blast_radius: one block of the Team page changes look: a head row in each metric group, the
  stripe moves to the second row, names turn semi-bold, 26px under each group heading.

approved_design:
  - team: #134

decisions_taken: >
  The registry is the standard and the page follows it; no registry rule changes (approved in chat,
  2026-11-07). A head whose labels wrap aligns them at the top, so every group heading keeps its
  26px to the first label in every language.

decisions_reserved: none.

done_when:
  - python -m pytest tests passes.
  - npm run build and the design check pass in site_v2.
  - The Team page's Performance tab passes the Table and Metric group heading rules at every listed width and language.

acceptance_criteria:
  - "Each metric group's table in Compared with last season has its own head row, and its rows line up with it."
  - "Rows are striped from the second row, with the switch off and on."
  - "Names in the table are 14px semi-bold ink."
  - "Each metric group heading sits 26px above its table."
  - "Measured on the Team page with the Performance tab open at 280, 320, 360, 375, 700 and 1010px in EN, DE and FI."

amendments: (none)
