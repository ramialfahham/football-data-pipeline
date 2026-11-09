# Task contract — a class the component registry lists is not a design gap

objective: >
  Issue #270. The design check's `classes` count names the classes on a page that nothing in the
  design chain knows. It read only the block standard's selectors, so the 34 registry parts still
  marked `gap` were counted again on every page, and a new page that uses the site frame arrived
  above zero. The check now takes every class `docs/design/components.yml` lists as known; the
  registry's own gap count keeps pinning the open parts. The Player page (#259) follows.

refs: >
  #270, approved in chat, 2026-11-09.

scope_paths:
  - .claude/task/270-registry-classes/
  - scripts/check_design_inventory.py
  - tests/test_design_inventory.py
  - tests/fixtures/design_inventory/*
  - docs/wireframes/block_standard.md

protected_override: >
  scripts/check_design_inventory.py and tests/test_design_inventory.py: the `classes` count takes
  the registry's classes as known, and a test pins it. Approved in chat, 2026-11-09, with the
  block_standard.md line that names the count.

impact_map: >
  writers: none in the warehouse.
  lineage: no dbt model changes, so no lineage moves.
  guard: check_design_inventory.py runs in validate:ui (.gitlab-ci.yml) and locally; the changed
  set feeds only COUNT_JS's `classes` count, through the `registered` list passed to each render.
  The element assertions, the other four counts, the coverage gaps and scripts/check_page_css.py
  (which reads design_inventory.class_tokens itself) are unchanged. If the registry fails to load
  the check stops with an error, never with a lower count. What stops being caught: a page class
  the registry lists but no rule measures; the registry's gap count in
  tests/fixtures/component_registry/baseline.json still pins each such part.
  ci_layer_rules: scripts/check_design_inventory.py, scripts/check_component_registry.py.
  deploy_order: before the Player page (#259). One merge.
  blast_radius: every built page's and mock's `classes` pin falls to the classes the registry
  does not list, in baseline.json and baseline_quick.json; no other count moves; nothing a reader
  sees changes.

decisions_taken: >
  The registry is the list of the site's parts, so a class it lists is known; a part with no rule
  yet is the registry's own gap, counted once there (approved in chat, 2026-11-09).

decisions_reserved: none.

done_when:
  - python -m pytest tests passes.
  - The design check at the merge request's scope fails only on counts that fell, and the class pins are lowered to them.
  - No design pin rises above main's.

amendments: (none)
