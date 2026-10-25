# Task contract — the correction check compares every goal

objective: >
  assert_result_corrections_applied calls a goal correction no longer needed only when the
  provider has every goal as the seed has it: same team, same player id and same minute; a seed
  goal without a player id never matches. The five goal rows of CAF match 1639347 stay, and the
  nightly passes the check again.

refs: >
  #232 (the goals of CAF match 1639347; the check's rule approved in chat, 2026-10-25).

scope_paths:
  - dbt_project/tests/assert_result_corrections_applied.sql
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md

impact_map: >
  writers: none; the change is in one singular dbt test. downstream: the test reads
  fixture_result_corrections, standings_corrections, fixture_goal_corrections,
  base_apif__fixtures_next, base_apif__standings and base_apif__fixture_events, and nothing reads
  the test except dbt's build order, which skips the nodes after it when it fails. layer_rules: a
  test changes no model, seed or served column. deploy_order: none; the nightly runs main.
  blast_radius: one problem class of one test (no_longer_needed on fixture_goal_corrections).

approved_design: []

acceptance_criteria:
  - "The check names a goal correction no_longer_needed only when every seed goal has a provider goal with the same team, player id, minute and added minute, one to one; a seed goal without a player id never matches."
  - "The check on prod's data returns no row; the check as on main returns the 1639347 row on the same data."
  - "The not_applied, does_not_add_up and not_sourced branches and the other two seeds' checks are unchanged."

decisions_taken: >
  Approved in chat, 2026-10-25: a goal correction is no longer needed only when the provider has
  every goal as the seed has it (same team, same player id, same minute); a seed goal without a
  player id never matches; the five rows of match 1639347 stay. Reading: the same minute means
  the same minute and the same added minute. No new dependency and no recurring cost.

decisions_reserved: []

done_when:
  - dbt parse passes and SQLFluff passes on the test.
  - The full pytest suite and the offline gates pass.
  - Reviewers per review_routing.json pass.
  - The check on prod's data returns no row; data:build:mr passes.

amendments: []
