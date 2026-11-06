# Task contract — fill a player's match from line-ups and goal events

objective: >
  Issue #256, note 4176079595. R4 loses its second half. For a played team match with no player
  data, a player's inputs come from that match's line-ups and goal events, as a cleaning step in
  the models. Metrics that need provider stats stay blank by R4's remaining sentence.

refs: >
  #256 note 4176079595; plan approved in chat 2026-11-06.

scope_paths:
  - dbt_project/models/docs/metric_rules.md
  - dbt_project/models/2_base/api_football/base_apif__fixture_players_from_lineups.sql
  - dbt_project/models/2_base/api_football/base.yml
  - dbt_project/models/3_core/fct_fixture_player_stats.sql
  - dbt_project/models/3_core/core.yml
  - dbt_project/models/4_intermediate/shared/int_legs__player_match.sql
  - dbt_project/models/4_intermediate/shared/int_legs__team_from_players.sql
  - dbt_project/models/4_intermediate/shared/int_legs.yml
  - dbt_project/models/4_intermediate/shared/int_player_club_season__metrics.sql
  - dbt_project/models/4_intermediate/shared/int_player_momentum__metrics.sql
  - dbt_project/models/4_intermediate/shared/int_player_profile__contribution.sql
  - dbt_project/models/4_intermediate/shared/int_player_season_position__metrics.sql
  - dbt_project/models/4_intermediate/shared/int_player_season_record.sql
  - dbt_project/models/4_intermediate/shared/int_team__current_national_competitions.sql
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_player_season__metrics.sql
  - dbt_project/models/5_marts/shared/mart_player_fixture_stats.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/models/docs/shared_columns.md
  - dbt_project/docs/layering.md
  - dbt_project/macros/team_seasons_without_player_data.sql
  - dbt_project/seeds/fixture_goal_corrections.csv
  - dbt_project/seeds/player_match_cleaning_answer_key.csv
  - dbt_project/seeds/schema.yml
  - dbt_project/tests/assert_mart_player_fixture_stats_keeps_every_stat_line.sql
  - dbt_project/tests/assert_stat_facts_equal_base.sql
  - dbt_project/tests/assert_player_metrics_follow_catalogue_formula.sql
  - dbt_project/tests/assert_player_match_cleaning_answer_key.sql
  - dbt_project/tests/assert_players_from_lineups_goals_add_up.sql
  - tests/**
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md

impact_map: >
  writers: base_apif__fixture_players_from_lineups is new and is written only by dbt. It reads
  base_apif__lineups, base_apif__fixture_events, base_apif__fixture_players and
  base_apif__fixtures_next. base_apif__lineups already reads base_apif__fixture_players, so the fill
  cannot live inside that model. fct_fixture_player_stats gains a union and the column
  is_from_lineups; its only writer stays dbt, and it stays a full table rebuild.

  downstream: `dbt ls --select fct_fixture_player_stats+ --resource-type model` lists
  int_legs__player_match, int_legs__team_from_players, int_player__page_profile,
  int_player_club_season__metrics, int_player_competition_benchmark_metrics_long,
  int_player_competition_benchmarks, int_player_match__metrics, int_player_momentum__metrics,
  int_player_page__window_seasons, int_player_profile__contribution, int_player_profile__yoy,
  int_player_season__metrics, int_player_season__team, int_player_season_position__metrics,
  int_player_season_record, int_player_squad_window__metrics, int_player_window__metrics,
  int_team__current_national_competitions, int_team_competition_benchmark_metrics_long,
  int_team_competition_benchmarks, int_team_momentum__metrics, int_team_profile__yoy,
  int_team_season__deserved_vs_actual, int_team_season__metrics,
  int_team_season__metrics_cumulative, int_team_season_record, mart_competition_fixtures,
  mart_leaderboards, mart_match_days, mart_matchday_insights, mart_player_career,
  mart_player_competition_benchmarks, mart_player_fixture_stats, mart_player_momentum,
  mart_player_profile, mart_player_season_record, mart_player_squad_benchmarks,
  mart_player_window_metrics, mart_team_competition_benchmarks, mart_team_competitions,
  mart_team_index, mart_team_leaderboards, mart_team_momentum_window, mart_team_profile,
  mart_team_season, mart_team_season_insights, mart_team_season_record, mart_team_window_metrics.
  Every team model in that list reads the players through int_legs__team_from_players, which
  leaves the filled rows out, so team values do not move. mart_player_fixture_stats carries a
  filled row's values with has_stat_line false: has_stat_line keeps its meaning, the provider sent
  a statistics line. So mart_team_momentum_window.has_player_stats, its only model reader, does
  not move. The export's player log reads the mart without that filter: its rows and has_stat_line
  stay, and filled values appear where blanks stood. match_involvement says played for a filled row
  with minutes, and neither played nor on_bench for one with blank minutes. The tests that compare
  the fact with its base or the mart with the fact, assert_stat_facts_equal_base and
  assert_mart_player_fixture_stats_keeps_every_stat_line, learn the filled rows.

  layer_rules: check_layer_contract.py. The new model is 2_base and reads only base models and
  seeds. Core reads base. No model declares partition_by or cluster_by. No per-competition file.

  deploy_order: one MR, no raw change, no ingest change. The MR build writes its own ci_mr tables.
  After the merge, the next build of main and the 04:00 nightly rebuild prod.

  blast_radius: player metrics, player marts and the player rows of the export change. Values
  appear where blanks stood, in competitions with filled matches: 6,480 matches can be filled, 569
  of them this season. Goals, assists, minutes, appearances, starts and a keeper's goals conceded
  move. Team metrics do not. Visible: the Team page Squad tab, leaderboards, top players on match
  previews, and the minutes on the team sheet of a filled Match page. No layout change.

approved_design:
  - none: no site or export file changes; values appear in existing slots, named in the plan

decisions_taken: >
  R4's text is the one approved on #256, note 4176079595. The plan approved in chat 2026-11-06
  names these readings. A team match with no usable line-up still blanks the player's window,
  because its input is missing. Only confirmed or researched sheets fill. Cards are not filled; a
  sending-off only ends a player's minutes. A shoot-out match counts 120 minutes only where an event
  stands past minute 90. A new match with a usable line-up and wrong goal events fails the build
  until it is researched. The new model name and is_from_lineups stood in that plan. The fact
  unions two bases of one endpoint, as that plan names; the layer contract's union rule is about
  competitions. By the Blank rule, minutes stay blank in a match whose sheets show no substitution
  and for a substitute with no minute on who scored or assisted. NEW MECHANISM:
  none; this is one more cleaning step, approved on #256. RECURRING COST: one small base table in
  the nightly, measured in the MR build.

decisions_reserved:
  - none: the Club tab question for players with no club football stays open on #256, outside this task

done_when:
  - metric_rules.md R4 reads exactly "R4 A metric is blank when any match it counts lacks an input."
  - dbt parse passes; SQLFluff passes on every changed model.
  - pytest tests passes.
  - data:build:mr is green, with assert_players_from_lineups_goals_add_up and
    assert_player_match_cleaning_answer_key passing.
  - The new blank counts stand on #256.

amendments: (none)
