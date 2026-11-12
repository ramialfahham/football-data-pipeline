# Task contract — Players to watch: the two boards' ranks in the season record

objective: >
  Issue #132 (Players to watch, notes of 2026-11-10): serve each upcoming match side's two boards
  from mart_player_season_record. Goals and assists ranks outfield players by goals plus assists,
  then goals, then fewer minutes. Ball actions per 90 ranks outfield players with at least a third
  of the team's minutes in the window, by the value, then more minutes. The window stays the
  match's own competition this season, or last season before the team's first match in it.

refs: >
  #132 notes of 2026-11-10 (Players to watch: window, two boards, top 3, outfield only, the floor
  of mart_player_squad_benchmarks); stream D plan, go from the coordinating session on 2026-11-12.

scope_paths:
  - scripts/generate_metric_sql.py
  - dbt_project/models/4_intermediate/shared/int_player_season_record.sql
  - dbt_project/models/4_intermediate/shared/int_season_record.yml
  - dbt_project/models/5_marts/shared/mart_player_season_record.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/models/docs/metric_columns.md
  - dbt_project/seeds/metric_map.csv
  - dbt_project/tests/assert_player_season_record_board_ranks.sql
  - tests/test_generate_metric_sql.py
  - .claude/task/132-players-to-watch-data/contract.md
  - .claude/task/132-players-to-watch-data/review.md
  - .claude/task/132-players-to-watch-data/review_input.patch

impact_map: >
  writers: dbt only; no ingestion change. int_player_season_record gains one generated column,
  ball_actions_per90, the catalogue formula over the running window. mart_player_season_record
  gains ball_actions_per90, team_matches, scorer_points_rank and ball_actions_per90_rank; no grain
  change, no existing column changes.
  lineage: `dbt ls --resource-type model --select int_player_season_record+` returns
  int_player_profile__yoy, int_player_season_record, mart_player_index, mart_player_profile,
  mart_player_season_record. int_player_profile__yoy names its columns, so the new column stops
  there; mart_player_index and mart_player_profile read int_player_profile__yoy's named columns.
  consumption: scripts/export_site_data.py reads mart_player_season_record with `select *` and
  keeps every column but _TOPPLAYER_DROP, so the match payload's players gain the four new keys
  until the Players to watch build (stream C) reads them; the page renders none of them.
  layer_rules: check_layer_contract.py (marts read intermediates and core, no mart-from-mart);
  generated metric SQL checked by tests/test_generate_metric_sql.py.
  deploy_order: additive columns; the deployed models keep working until the merge, and the
  nightly picks the change up after it.
  blast_radius: mart_player_season_record (4 new columns), int_player_season_record (1 new
  column); no existing value changes.

approved_design:
  - none: no page output changes

decisions_taken: >
  The board rules are the #132 notes of 2026-11-10 (approved in chat). Outfield means the
  window's own position to date is not G; a player with no known position counts as outfield
  unless dim_player says goalkeeper. The floor is the team's played matches in the window (awarded
  results not counted) x 90 / 3, as mart_player_squad_benchmarks counts it. top_player_rank stays
  until the page build replaces its reader. The ranks are row_number: each board shows exactly
  three rows per side.

decisions_reserved:
  - none: every rule applied is in the #132 notes of 2026-11-10

done_when:
  - python scripts/generate_metric_sql.py --check passes
  - python scripts/sync_metric_docs_blocks.py --check passes
  - dbt parse passes; sqlfluff lint of the two models passes
  - full pytest passes
  - the new singular test and the mart's ranks hold on a read-only query against the CI build

amendments: (none)
