# Task contract — the design-check counters count only what the registry forbids

objective: >
  The design checks count a designed hyphen break of a club name as a split, and count a page
  that has no matches to show as missing Fold, Match row score or Filter row. Both are false
  counts. Fix the counters so a break at a hyphen is a split only where the registry does not
  allow it, and an element is expected only on a page whose rows would show it. Re-measure the
  pins; none rises.
refs: "#231, !490 (the Result row part club-name), #297 (blocked by the false rises)"

scope_paths:
  - scripts/check_design_inventory.py
  - scripts/design_inventory.py
  - scripts/check_component_registry.py
  - docs/design/components.yml
  - tests/test_design_inventory.py
  - tests/test_check_component_registry.py
  - tests/fixtures/design_inventory/baseline.json
  - tests/fixtures/design_inventory/baseline_quick.json
  - tests/fixtures/design_inventory/baseline_quick_fi.json
  - .claude/task/231-check-counts/contract.md
  - .claude/task/231-check-counts/review.md
  - .claude/task/231-check-counts/review_input.patch

protected_override: >
  The coordinating session approved the change to the design checks and to the one registry
  key, in the session message of 2026-11-20, as an engineering decision under the CPO's
  visual-details mandate of 2026-11-16 (the counters were wrong, not the pages). The MR head
  declares the locked files; the CPO's merge is the approval.

impact_map: >
  writers: none. No table or model is written. The files are checks and their tests.
  downstream: the guards' readers. `scripts/check_design_inventory.py` runs in `ci_local --mr`
  (job validate:ui and the MR design job) and in the main sweep against
  tests/fixtures/design_inventory/baseline.json and baseline_quick*.json;
  `scripts/design_inventory.py` is imported by it and by tests/test_design_inventory.py;
  `scripts/check_component_registry.py` reads docs/design/components.yml and generates
  docs/wireframes/block_standard.md, whose generated table is pinned by a test. Nothing else
  reads the `breaks` key (grep over scripts, tests, design-mocks, site_v2/src: only
  check_component_registry.py).
  layer_rules: none apply (no dbt). The registry's own checker validates the new `breaks` value.
  deploy_order: none. No deployed system reads these files; the nightly never runs them.
  blast_radius: what stops being counted is a break at a hyphen inside a part marked
  `breaks: hyphens` where the word is wider than its line, and an element missing from a page
  that has no row that would show it. Every other split, overflow, scroll, overlap and
  miss still counts, and the registry's three Fold, Match row score and Filter row rows
  stay expected wherever their rows exist. A pin may only fall.

approved_design:
  - none: no page output changes

depends_on:
  - none: no open MR touches the checks, the registry or the baselines (the only open MR, !491, is seeds)
shared_files:
  - tests/fixtures/design_inventory/baseline.json
  - tests/fixtures/design_inventory/baseline_quick.json
  - tests/fixtures/design_inventory/baseline_quick_fi.json

decisions_taken: >
  A part of the registry that may break a word at its hyphens says so with `breaks: hyphens`,
  read by the check; the check never parses the rule text. The part club-name is the only one
  marked. A word broken at hyphens inside such a part is not a split when every break falls
  right after a hyphen and the word is wider than its box. Fold, Match row score and Filter row
  are expected on the Matches page and the Matches day page only when the page's rows would
  show them: a competition group with more than 3 rows (VISIBLE_ROWS of MatchesDay.astro), a
  row whose two scores differ (MatchRow.astro marks a winner only then), at least 2 distinct
  entity types or 2 distinct confederations among the groups (FilterRows.astro shows a filter
  from 2 values). The precondition reads the rows, never the element it excuses. The task was
  assigned and the registry key approved by the coordinating session. No new recurring cost.

decisions_reserved:
  - none: the three counters follow the registry's own rules and the page code's own thresholds, and nothing new about a page is decided

done_when:
  - tests/test_design_inventory.py and tests/test_check_component_registry.py pass, including the new tests (a hyphen break allowed, a non-hyphen split counted, a break outside the allowed part counted, a break where the word fits counted, a thin day page not counted, a full day page without its Fold still counted).
  - python scripts/check_component_registry.py is green and docs/wireframes/block_standard.md is regenerated unchanged.
  - python scripts/ci_local.py --mr is green and every pin is at or below main's.
  - The MR pipeline is green.

amendments: (none)
