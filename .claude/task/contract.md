# Task contract — a team-wide match order in mart_team_fixtures

objective: >
  The Team page's Matches tab lists one team's upcoming matches and its results across every
  competition it plays. mart_team_fixtures ranks rows only within one competition-season, so the
  mixed lists have no order from the warehouse, and layering.md §Consumption layer forbids
  ordering them in the export. Two columns add that order: upcoming_order and result_order.

refs: >
  #235 (column names approved in chat, 2026-10-30; this order lands in its own MR before the Team
  page MR switches the export to it).

scope_paths:
  - dbt_project/models/5_marts/shared/mart_team_fixtures.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch

impact_map: >
  writers: mart_team_fixtures is written only by dbt (the fdp-nightly prod build, and data:build:mr
  into ci_mr<IID>_marts); it reads fct_fixture, dim_team and int_legs__team_match, none of which
  changes. downstream: `dbt ls --select mart_team_fixtures+` (run 2026-10-30 on this branch's base)
  lists the model and its 11 tests and no downstream model:
  mart_team_fixtures, accepted_values_mart_team_fixtures_result__W__D__L,
  dbt_utils_unique_combination_of_columns_mart_team_fixtures_team_sk__fixture_sk,
  not_null_mart_team_fixtures_fixture_sk, not_null_mart_team_fixtures_league_code,
  not_null_mart_team_fixtures_team_sk,
  relationships_mart_team_fixtures_fixture_sk__fixture_sk__ref_fct_fixture_,
  relationships_mart_team_fixtures_opponent_team_sk__team_sk__ref_dim_team_,
  relationships_mart_team_fixtures_team_sk__team_sk__ref_dim_team_,
  team_fixtures_ranks_positive, team_fixtures_recency_has_result, team_fixtures_result_present.
  Outside dbt the only reader is scripts/export_site_data.py, which selects * filtered on
  upcoming_rank/recency_rank and keeps only _TEAM_FIXTURE_FIELDS, so the new columns are dropped
  and no payload changes. layer_rules: 5_marts consumption layer, materialised as a table at
  project level (check_layer_contract.py); all ordering comes from the warehouse
  (layering.md §Consumption layer). deploy_order: additive columns on a table rebuilt whole; the
  first fdp-nightly after merge adds them to prod, and nothing reads them until the Team page MR
  merges. blast_radius: no existing column or number changes; two new nullable integer columns.

approved_design:
  - none: no page output changes

decisions_taken: >
  Column names upcoming_order and result_order, approved in chat, 2026-10-30. upcoming_order
  numbers every is_upcoming row of a team across all its competitions and seasons, soonest
  kick-off first, ties by fixture_sk; result_order numbers every has_result row of a team within
  one season_api_year across all its competitions, newest kick-off first, ties by fixture_sk
  descending; both null on other rows. Existing columns unchanged. Tests: each order null exactly
  when its flag is false, positive, and unique per partition. No new mechanism, dependency or
  recurring cost: two window functions in a model the nightly already builds.

decisions_reserved:
  - Any change to an existing column's values, or to an export or page, stops the task and goes to
    the CPO.

done_when:
  - dbt parse passes; sqlfluff lint on the model is clean; pytest tests and the offline gates pass.
  - data:build:mr is green, including the new tests.
  - The prod comparison (main's SQL against ci_mr<IID>_marts.mart_team_fixtures, every existing
    column both ways with except distinct) returns zero rows, its dry-run bytes put to the CPO
    first.

amendments: (none)
