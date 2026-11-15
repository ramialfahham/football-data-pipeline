# Task contract — lower the main-scope design-inventory baseline

objective: >
  After the phone fixes merged, main's full sweep reports three counts that fell
  (Competitions index overflow, Match page overflow, Match page scroll). Lower them in
  baseline.json so main's validate:ui is green. Pins only go down.

refs: >
  #231, MR 439 (merged as 662fb423), main pipeline 3070264174 job 18043100743.

scope_paths:
  - tests/fixtures/design_inventory/baseline.json
  - .claude/task/231-baseline-lower/contract.md
  - .claude/task/231-baseline-lower/review.md
  - .claude/task/231-baseline-lower/review_input.patch

approved_design:
  - none: no page output changes

decisions_taken: >
  Competitions index overflow 42 to 0 (key dropped, as compare_rendered drops zero counts),
  Match page overflow 12 to 0 (key dropped), Match page scroll 2184 to 2175. No count rises.
  The task was assigned by the coordinating session. No new mechanism, no recurring cost.

decisions_reserved:
  - none: the three lowered counts are the ones the failed job reports and nothing else changes.

done_when:
  - The design inventory in the full main scope, run in the CI image mcr.microsoft.com/playwright/python:v1.63.0-noble over a built site_v2/dist, shows 0 failures.
  - The MR pipeline is green.

amendments: (none)
