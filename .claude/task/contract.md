# Task contract — a table that opens with the name keeps it in the first column in its narrow form

objective: >
  Issue #264. In a table whose rows start with the name, the two-line narrow form keeps the name in
  the first column, as the registry's Table narrow row says. Today the form places the name from the
  second column, written for tables that open with a rank, so Compared with last season on the Team
  page puts its names over the number columns at 280px in DE and FI. The Player page (#259) reuses it.

refs: >
  #264, approved in chat 2026-11-07. Design: #134.

scope_paths:
  - site_v2/src/styles/system.css
  - tests/fixtures/design_inventory/*
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md

protected_override: none.

impact_map: >
  writers: none in the warehouse.
  lineage: no dbt model changes, so no lineage moves.
  consumption: every `.ctab` whose rows open with the name cell, in its narrow form (fit-two, or no
  fit mark below a 600px container). Today: Compared with last season and the Team page's deserved
  points table (`.dpm`), which is marked fit-one at every listed width, so it does not change.
  ci_layer_rules: scripts/check_page_css.py, scripts/check_design_inventory.py,
  scripts/check_component_registry.py.
  deploy_order: before the Player page (#259). One merge.
  blast_radius: the Team page's Performance tab at the widths where Compared with last season takes
  two lines: its names move back to the first column.

approved_design:
  - team: #134

decisions_taken: >
  The registry is the standard and the page follows it; no registry change (approved in chat,
  2026-11-07).

decisions_reserved: none.

done_when:
  - python -m pytest tests passes.
  - npm run build and the design check pass in site_v2.
  - On the Team page's Performance tab, every name of Compared with last season starts in the first column at every listed width and language.

acceptance_criteria:
  - "In the narrow form of a table whose rows open with the name, the name spans from the first column."
  - "A table that opens with a rank keeps its narrow form unchanged."
  - "Measured on the Team page with the Performance tab open at 280, 320, 360, 375, 700 and 1010px in EN, DE and FI."

amendments: (none)
