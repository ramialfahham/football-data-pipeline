# Task contract — one player-in-a-match mart

objective: >
  mart_player_fixture_stats absorbs mart_player_match_log and becomes the one mart for a player
  in a finished match: the match context (opponent, the team's score, the result, crests) joins
  the columns it has, and mart_player_match_log is deleted. Every reader of the match log moves
  to it. Every count and rate a reader showed before it shows after; the flags is_starter,
  is_substitute and position_code come from the checked line-ups, as they already do on
  mart_player_fixture_stats, and the match-log rows where they change are counted and listed
  before merge.

refs: >
  #176 (https://gitlab.com/rami.al-fahham/football-data-pipeline/-/work_items/176), the line
  "mart_player_match_log and mart_player_fixture_stats become one mart". Kept name, the pair
  team_goals_for / team_goals_against, and the line-up flags: approved in chat, 2026-10-13.

scope_paths:
  - dbt_project/models/5_marts/shared/mart_player_fixture_stats.sql
  - dbt_project/models/5_marts/shared/mart_player_match_log.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/tests/assert_player_metrics_follow_catalogue_formula.sql
  - dbt_project/seeds/metric_map.csv
  - dbt_project/models/docs/metric_columns.md
  - dbt_project/docs/layering.md
  - scripts/generate_metric_sql.py
  - scripts/export_site_data.py
  - tests/test_metric_map.py
  - tests/test_export_site_data.py
  - tests/test_no_decision_history_in_code.py
  - tests/test_no_decision_history_in_docs.py
  - docs/site_architecture.md
  - docs/content_architecture.md
  - docs/wireframes/03_player_profile.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md

impact_map: >
  writers: dbt builds mart_player_fixture_stats and mart_player_match_log from
  fct_fixture_player_stats, fct_fixture_lineup, fct_fixture, dim_player and dim_team. No ingestion
  writer.
  downstream: dbt ls --select mart_player_match_log+ mart_player_fixture_stats+ (dbt 1.7.20, on
  the branch's base) returns the models mart_player_fixture_stats, mart_player_match_log,
  mart_team_momentum_window and the singular tests assert_mart_player_fixture_stats_keeps_every_stat_line,
  assert_momentum_window_matches_momentum, assert_player_metrics_follow_catalogue_formula,
  assert_tournament_form_window. mart_player_match_log has no dbt reader but its own tests and
  assert_player_metrics_follow_catalogue_formula. Outside dbt: scripts/export_site_data.py
  (fetch_player_payloads reads the match log; fetch_matchstats_payloads reads
  mart_player_fixture_stats), scripts/generate_metric_sql.py (one Surface per mart),
  seeds/metric_map.csv and models/docs/metric_columns.md (generated from shared.yml by
  scripts/sync_metric_docs_blocks.py), tests/test_metric_map.py (fan question 19). site_v2/src
  reads neither payload's fields.
  layer_rules: marts read core and dims only; no new model, no new mart; check_layer_contract
  unchanged.
  deploy_order: the merged mart builds in data:build:mr and in the first nightly after merge.
  The player export reads the new columns only after that build; the old table
  marts.mart_player_match_log stays in prod until the CPO drops it.
  blast_radius: mart_player_match_log disappears; mart_player_fixture_stats gains seven columns
  (opponent_team_sk, team_goals_for, team_goals_against, team_logo_url, opponent_name,
  opponent_logo_url, result) and keeps every existing value. The player payload is read with the
  same keys and values apart from is_starter, is_substitute and position_code on the rows the
  line-ups correct; the match-stats payload is unchanged.

decisions_taken: >
  Merged mart keeps the name mart_player_fixture_stats; the match-log score pair is named
  team_goals_for and team_goals_against, the goalkeeper's goals_against keeps its name; flags
  from the checked line-ups with the changed rows counted before merge: approved in chat,
  2026-10-13. No new mechanism, no new dependency.

  THRESHOLD DECLARATIONS: NEW MECHANISM: none. RECURRING COST: expected to fall, one mart build
  less per nightly; measured before and after and put to the CPO in GiB.

decisions_reserved:
  - Dropping the orphaned prod table marts.mart_player_match_log after merge.
  - The one-match window mart's name, mart_leaderboards as a window of one, and removing
    mart_team_fixture_stats: later lines of #176, not this change.
  - design-mocks/gen_match_page.py text that says two marts serve one stat line: belongs to the
    played match page, #175.

done_when:
  - dbt parse passes; dbt compile of mart_player_fixture_stats passes; sqlfluff lint of the mart is clean.
  - python scripts/generate_metric_sql.py --check and the pytest files test_metric_map, test_generate_metric_sql, test_sync_metric_docs_blocks, test_export_site_data pass.
  - data:build:mr is green on the MR, its tests included.
  - On prod data, the merged mart where has_stat_line against the old match log has the same key set and the same value in every shared column except the line-up flags; those are counted per column and listed.
  - On prod data, the merged mart against the old mart_player_fixture_stats shows no difference on that mart's own columns.
  - The nightly warehouse read of the two marts before and after is measured and put to the CPO.

amendments: >
  Added tests/test_no_decision_history_in_code.py to scope_paths: deleting
  mart_player_match_log.sql removes flagged comment lines, and the test pins the count in both
  directions, so its two pin numbers go down to the new count. Likewise
  tests/test_no_decision_history_in_docs.py: the Player profile wireframe loses its dated
  "verified" note when it names the merged mart, so that file's pin goes from 4 to 3.
  Authority: the pins' own instruction to lower them when a cleanup removes lines; no behaviour
  changes.
  docs/site_architecture.md: the one replacement of the mart list in the Player profile row
  was approved as exact text in chat, 2026-10-13.
