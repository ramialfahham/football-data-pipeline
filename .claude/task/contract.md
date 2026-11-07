# Task contract — the Team page's Performance tab passes every registry rule the design check measures

objective: >
  Issue #266. With the Performance tab open, the Team page fails three registry rules: the deserved
  points table sets its names to weight 400 (Table name cell: 600), the metric group headings over the
  strips sit 10–12px above their first row (Metric group heading: 26px), and Compared with last
  season's head label "Vorsaison" is wider than its column at narrow widths and overlaps "Trend". In
  the narrow deserved points chart a long team name runs across the y-axis numbers. The page follows
  the registry. The Player page (#259) reuses the strips and the table.

refs: >
  #266, approved in chat 2026-11-07. Design: #134.

scope_paths:
  - site_v2/src/styles/system.css
  - site_v2/src/components/team/*
  - site_v2/src/lib/chartTheme.ts
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
  consumption: `.ctab.dpm` and the deserved points chart (TeamDeserved), the strip group heading and
  `.rs-val` (TeamLeagueStrips) and `.ctab.yoyt` (TeamLastSeason), all on the Team page's Performance
  tab. The match page's metric comparison (`.cmp .rkgroup`) has no `.rs-row` and does not change.
  ci_layer_rules: scripts/check_page_css.py, scripts/check_design_inventory.py,
  scripts/check_component_registry.py, site_v2/scripts/check-built-pages.mjs.
  deploy_order: before the Player page (#259). One merge.
  blast_radius: the Team page's Performance tab only: deserved points names turn semi-bold, 16px more
  air under each strip group heading, the strip value sits at the row's top (2px up in the wide row),
  and the last-season table's value columns widen from 3.4rem to 4.2rem and the trend from 2.8rem to
  3.2rem below a 420px container. In the deserved points chart the team's name sits on the side of
  its dot where it fits; where neither side fits, the name and the difference stack centred on the
  dot, inside the plot. Today that is the long names in the narrow chart.

approved_design:
  - team: #134

decisions_taken: >
  The registry is the standard and the page follows it; no registry change (approved in chat,
  2026-11-07).

decisions_reserved: none.

done_when:
  - python -m pytest tests passes.
  - npm run build and the design check pass in site_v2.
  - On a build whose Team pages open on the Performance tab, the design check reports none of the three failures, and no page overlaps at 280, 320 or 360px.

acceptance_criteria:
  - "Names in the deserved points table are 14px semi-bold ink."
  - "Each metric group heading over the strips sits 26px above the first line of its first row."
  - "Compared with last season's head labels fit their columns: no overflow and no overlap in EN, DE and FI."
  - "In the deserved points chart the team's name crosses no axis label."
  - "Measured on the Team page with the Performance tab open at 280, 320, 360, 375, 700 and 1010px in EN, DE and FI."

amendments: (none)
