# Task contract — Player page data: every value on both tabs served by a tested model

objective: >
  Issue #256: build the marts the Player page (#136) reads, so its tab builds start from finished
  tables instead of hand-pulled mock data. Data only: no site, no system.css, no components.yml,
  no export.

refs: >
  #256, plan approved in chat 2026-11-05. Design: #136.

scope_paths:
  - dbt_project/seeds/metric_catalogue.csv
  - dbt_project/seeds/metric_map.csv
  - dbt_project/seeds/player_season_answer_key.csv
  - dbt_project/seeds/player_window_answer_key.csv
  - dbt_project/seeds/schema.yml
  - dbt_project/macros/player_benchmark_metrics.sql
  - dbt_project/macros/competition_type_order.sql
  - dbt_project/macros/team_seasons_without_player_data.sql
  - dbt_project/models/2_base/api_football/base_apif__squads.sql
  - dbt_project/models/2_base/api_football/base.yml
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_player_season__metrics.sql
  - dbt_project/models/4_intermediate/shared/int_competition_season__club_windows.sql
  - dbt_project/models/4_intermediate/shared/int_team__current_national_competitions.sql
  - dbt_project/models/4_intermediate/shared/int_player__page_profile.sql
  - dbt_project/models/4_intermediate/shared/int_player_page__window_seasons.sql
  - dbt_project/models/4_intermediate/shared/int_player_window__metrics.sql
  - dbt_project/models/4_intermediate/shared/int_player_squad_window__metrics.sql
  - dbt_project/models/4_intermediate/shared/int_player_page.yml
  - dbt_project/models/4_intermediate/shared/int_player_season_position__metrics.sql
  - dbt_project/models/4_intermediate/shared/int_player_competition_benchmark_metrics_long.sql
  - dbt_project/models/4_intermediate/shared/int_competition_benchmarks.yml
  - dbt_project/models/4_intermediate/shared/int_player_season_position.yml
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season.yml
  - dbt_project/tests/assert_player_page_windows.sql
  - dbt_project/models/5_marts/shared/mart_player_profile.sql
  - dbt_project/models/5_marts/shared/mart_player_competition_benchmarks.sql
  - dbt_project/models/5_marts/shared/mart_player_fixture_stats.sql
  - dbt_project/models/5_marts/shared/mart_player_window_metrics.sql
  - dbt_project/models/5_marts/shared/mart_player_squad_benchmarks.sql
  - dbt_project/models/5_marts/shared/mart_team_competitions.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/models/docs/metric_rules.md
  - dbt_project/models/docs/metric_columns.md
  - dbt_project/tests/assert_player_metrics_follow_catalogue_formula.sql
  - dbt_project/tests/assert_player_window_answer_key.sql
  - dbt_project/tests/assert_player_season_answer_key.sql
  - dbt_project/docs/layering.md
  - scripts/generate_metric_sql.py
  - tests/test_catalogue_order.py
  - tests/test_no_decision_history_in_code.py
  - tests/test_generate_metric_sql.py
  - tests/test_metric_map.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md

impact_map: >
  writers: dbt only. RAW_APIF_SQUADS is written by ingestion/api_football/loads/squads.py and is
  unchanged. New models read it through stg_apif__squads.
  lineage: `dbt ls --resource-type model --select metric_catalogue+ int_player_season__metrics+
  int_player_season_position__metrics+ mart_player_profile+ mart_player_fixture_stats+
  int_player_competition_benchmark_metrics_long+` returns
  4_intermediate.domestic_league.team_season.int_player_season__metrics,
  4_intermediate.shared.int_player_competition_benchmark_metrics_long,
  4_intermediate.shared.int_player_competition_benchmarks,
  4_intermediate.shared.int_player_season_position__metrics,
  5_marts.shared.mart_leaderboards, 5_marts.shared.mart_player_competition_benchmarks,
  5_marts.shared.mart_player_fixture_stats, 5_marts.shared.mart_player_profile,
  5_marts.shared.mart_team_competition_benchmarks, 5_marts.shared.mart_team_leaderboards,
  5_marts.shared.mart_team_momentum_window.
  consumption: scripts/export_site_data.py reads mart_player_profile (is_featured_season, select
  star), mart_player_competition_benchmarks and mart_player_fixture_stats, and the catalogue's
  metric_order through the board order. New columns are not picked by its shapes. New benchmark
  metrics add entries to player payloads; no player page is built on the site.
  ci_layer_rules: scripts/check_layer_contract.py (intermediates never ref marts, no per-model
  materialisation, base refs staging or base only), scripts/generate_metric_sql.py --check,
  scripts/sync_metric_docs_blocks.py --check, scripts/check_description_hygiene.py.
  deploy_order: one merge; the nightly dbt build creates the new tables. No backfill, no ingest
  change, no new dependency.
  blast_radius: mart_player_profile gains columns, and is_featured_season changes only where two
  competitions tied (1,386 players today, an arbitrary pick). mart_player_competition_benchmarks
  gains five metrics and columns; rank stays by value descending, as the locked display contract
  reads it, and the new rank_best_first ranks by direction. mart_player_fixture_stats gains two columns. mart_team_competitions gives the same output.
  Two new marts, six new intermediates and base models. Rankings board order is unchanged:
  metric_order keeps the relative order of every board.

approved_design:
  - none: no page output changes

decisions_taken: >
  Plan, readings and the R6 text approved in chat 2026-11-05, recorded on #256. Model names follow
  mart_<entity>_<subject> and int_<domain>__<purpose>. A match with no player stats keeps the
  existing rule R4 until the open decision on #256 is made.
  The catalogue changes are the approved Metrics section of #136, copied as they stand.
  New rows, id: formula; group, direction, format, order:
  shots_per90: sum(shots) * 90 / sum(minutes); shooting, higher_better, decimal_1, 2.
  shots_on_goal_player_pct: sum(shots_on_target) / sum(shots); shooting, higher_better, percent, 5.
  fouls_per90: sum(fouls) * 90 / sum(minutes); discipline, lower_better, decimal_1, 2.
  offsides_per90: sum(offsides) * 90 / sum(minutes); discipline, lower_better, decimal_1, 6.
  goals_against_per90: sum(goals_against) * 90 / sum(minutes); goalkeeping, lower_better, decimal_1, 5.
  Descriptions and interpretations are #136's text word for word.
  is_key_metric true: scorer_points_per90, shots_on_goal_per90, passes_per90, ball_actions_per90,
  passes_key_per90, duels_won_per90, defensive_actions_per90.
  metric_order, each per-90 after its total as #136 rules:
  goals: goals_player, goals_per90, assists_player, assists_per90, scorer_points_player, scorer_points_per90.
  shooting: shots_player, shots_per90, shots_on_goal_player, shots_on_goal_per90,
  shots_on_goal_player_pct, finishing_efficiency_player_pct.
  passing: passes_player, passes_per90, passes_accuracy_player_pct, ball_actions_player,
  ball_actions_per90, passes_key_player, passes_key_per90.
  one_on_one: dribbles_attempts_player, duels_player, duels_won_player, duels_won_per90,
  duels_won_player_pct, dribbles_success_player, dribbles_success_per90, dribbles_success_player_pct.
  defending: defensive_actions_player, defensive_actions_per90, tackles_player, tackles_per90,
  interceptions_player, interceptions_per90, blocks_player, blocks_per90.
  goalkeeping: saves_player, saves_per90, saves_player_pct, goals_against_player, goals_against_per90.
  discipline: fouls_player, fouls_per90, cards_yellow_player, cards_red_player, offsides_player,
  offsides_per90.
  docs/wireframes/12_player_stats.md stays as it is: #136 retires it in the tab build.

decisions_reserved:
  - Whether the cards use line-ups and goal records for a match with no player stats, and the two sentences in #136 it touches.
  - What the Club tab shows for a player with no club football.

acceptance_criteria:
  - Every player has a season label, age, current club, position taken from match data, and a full name even when first or last name is missing.
  - A player in two leagues in the same year gets one featured season, chosen by the latest match.
  - Each player is marked with the tabs they have. National team comes from match data and the squad lists.
  - The four cards are served as totals, across the club competitions of the featured season, and across the current competitions.
  - Each nation has its current competitions, running now, otherwise the most recently finished.
  - The five new metrics, seven key metrics and new metric order are in the catalogue, as #136 sets out.
  - Fouls, offsides and goals against rank lowest-first.
  - Each position group has one player count for the explainer, and competitions come in the page's filter order.
  - Squad is served, with the teammates with at least a third of the team's minutes, each player's rank, the median and the count.
  - Each player has this season and last season over all club competitions at any club, with minutes on both sides.
  - Each match carries ball actions and which tab it belongs to.
  - Every new metric value has a value test against a hand-worked answer.
  - A match with no player stats gives a blank, as the existing rule says, until the open decision is made.

done_when:
  - dbt parse and dbt compile succeed from the repo root.
  - python -m pytest tests -q is green.
  - The offline gates in FAST_GATES pass.
  - CI's data:build:mr is green with every model inside BigQuery's 300-second limit.

amendments: (none)
