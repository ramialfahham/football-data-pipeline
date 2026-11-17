# Task contract — lower the four design-inventory pins that fell with !471

objective: >
  Issue #243: main's validate:ui (pipeline 3078457547, job 18101723045, on e15e5fbe) fails only on
  four rendered counts in the full design-inventory sweep that fell after !471 merged. This lowers
  exactly those four pins in tests/fixtures/design_inventory/baseline.json to the values main
  measured: Match page scroll 2175 to 2003; Team page overflow 3 to 0 (the entry goes);
  gen_matches_hub.py/matches-hub_2026-09-26.html scroll 9 to 8; matches hub scroll 9 to 8.

refs: >
  #243; !471; main pipeline 3078457547, job 18101723045 (its counts.json artifact is the source of
  the four values).

scope_paths:
  - .claude/task/243-lower-pins-471/
  - tests/fixtures/design_inventory/baseline.json

approved_design:
  - none: no page output changes

depends_on:
  - none: !471 is merged; the work is on main alone

shared_files:
  - tests/fixtures/design_inventory/baseline.json

decisions_taken: >
  A pin that fell is lowered to the measured value, as the check asks; no other pin moves. No new
  mechanism, dependency or recurring cost.

decisions_reserved:
  - none: lowering a fallen pin to its measured value is the check's own instruction.

done_when:
  - The four values in baseline.json equal main's counts.json for job 18101723045; no other value changes.
  - python scripts/ci_local.py --mr is green.

amendments: (none)
