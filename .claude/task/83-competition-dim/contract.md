# Task contract — competition facts in core dims; the export reads marts only

objective: >
  Issue #83: dim_league publishes the competition facts that are fixed for a competition and is
  the only reader of the competition_registry seed. dim_competition_season publishes the facts that
  can change between seasons (tier, competition_group), held per season in competition_season_map.
  Every model and dbt test reads the dims; scripts/export_site_data.py reads the marts dataset only.
  A CI check holds both lines.

refs: >
  #83. Plan approved in chat 2026-11-07; the revised plan, the removal of tier and
  competition_group from the registry, build_nav taking tier from mart_competition_index, and the
  two layering.md lines approved in chat, 2026-11-09. The name dim_league approved in chat,
  2026-11-09.

scope_paths:
  - docs/competition_registry.yml
  - dbt_project/seeds/competition_registry.csv
  - dbt_project/seeds/competition_season_map.csv
  - dbt_project/seeds/schema.yml
  - dbt_project/models/3_core/dim_league.sql
  - dbt_project/models/3_core/dim_competition_season.sql
  - dbt_project/models/3_core/core.yml
  - dbt_project/models/docs/shared_columns.md
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season__deserved_vs_actual.sql
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season__table_legs.sql
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season__table_state.sql
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season.yml
  - dbt_project/models/4_intermediate/shared/int_competition_season__club_windows.sql
  - dbt_project/models/4_intermediate/shared/int_legs__player_match.sql
  - dbt_project/models/4_intermediate/shared/int_legs__team_match.sql
  - dbt_project/models/4_intermediate/shared/int_player_page__window_seasons.sql
  - dbt_project/models/4_intermediate/shared/int_player_profile__yoy.sql
  - dbt_project/models/4_intermediate/shared/int_team__current_national_competitions.sql
  - dbt_project/models/4_intermediate/shared/int_team_competition_benchmark_metrics_long.sql
  - dbt_project/models/4_intermediate/shared/int_team_momentum_window.sql
  - dbt_project/models/4_intermediate/shared/int_team_profile__yoy.sql
  - dbt_project/models/5_marts/shared/mart_competition_fixtures.sql
  - dbt_project/models/5_marts/shared/mart_competition_index.sql
  - dbt_project/models/5_marts/shared/mart_leaderboards.sql
  - dbt_project/models/5_marts/shared/mart_next_matchday.sql
  - dbt_project/models/5_marts/shared/mart_player_career.sql
  - dbt_project/models/5_marts/shared/mart_player_fixture_stats.sql
  - dbt_project/models/5_marts/shared/mart_player_profile.sql
  - dbt_project/models/5_marts/shared/mart_player_season_record.sql
  - dbt_project/models/5_marts/shared/mart_roster.sql
  - dbt_project/models/5_marts/shared/mart_standings.sql
  - dbt_project/models/5_marts/shared/mart_team_competitions.sql
  - dbt_project/models/5_marts/shared/mart_team_index.sql
  - dbt_project/models/5_marts/shared/mart_team_leaderboards.sql
  - dbt_project/models/5_marts/shared/mart_team_profile.sql
  - dbt_project/models/5_marts/shared/mart_team_season_record.sql
  - dbt_project/models/5_marts/shared/mart_team_window_metrics.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/tests/assert_lineup_research_list.sql
  - dbt_project/tests/assert_mart_leaderboards_every_home_board_has_a_leader.sql
  - dbt_project/tests/assert_mart_next_matchday_competition_order_follows_the_key.sql
  - dbt_project/tests/assert_player_page_windows.sql
  - dbt_project/tests/assert_season_map_covers_club_editions.sql
  - dbt_project/tests/assert_team_benchmark_prev_season_matches_yoy.sql
  - dbt_project/tests/assert_team_form_window_follows_the_rule.sql
  - dbt_project/tests/assert_team_index_cup_rounds_scored.sql
  - dbt_project/tests/assert_team_index_one_winner_per_cup_season.sql
  - dbt_project/tests/assert_team_index_stage_answer_key.sql
  - dbt_project/tests/assert_team_yoy_pairs_the_same_games_played.sql
  - dbt_project/tests/assert_tournament_form_window.sql
  - dbt_project/docs/layering.md
  - scripts/export_site_data.py
  - scripts/sync_dbt_vars.py
  - scripts/check_registry_var_sync.py
  - scripts/check_layer_contract.py
  - .claude/skills/onboard-competition/SKILL.md
  - tests/test_check_layer_contract.py
  - tests/test_registry_seed_projection.py
  - tests/test_export_site_data.py
  - tests/test_export_landing.py
  - tests/test_export_matches.py
  - tests/test_catalogue_order.py
  - tests/test_sentence_length_in_docs.py
  - tests/test_no_decision_history_in_code.py
  - .claude/task/83-competition-dim/contract.md
  - .claude/task/83-competition-dim/review.md
  - .claude/task/83-competition-dim/review_input.patch
  - .claude/task/83-competition-dim/acceptance_evidence.md

impact_map: >
  writers: dbt only; no ingestion change. The registry YAML loses tier and competition_group;
  sync_dbt_vars.py stops projecting them, so the competition_registry seed loses both columns.
  competition_season_map gains tier and competition_group per (league_code, season_api_year),
  filled for every existing domestic-league row with today's registry value (19 leagues, all
  already mapped). dim_league gains the fixed facts from the seed and competition_types;
  dim_competition_season gains tier and competition_group from the map, a blank season taking the
  latest earlier season's value. Prod measured 2026-11-07: dim_league 48 rows, 48 distinct
  league_code, the same 48 codes as the seed both ways.
  lineage: `dbt ls --resource-type model --select dim_league+ dim_competition_season+
  competition_registry+ competition_season_map+` returns 72 models: dim_competition_season
  dim_league dim_player_team_season_mapping fct_standings int_competition_season__club_windows
  int_legs__player_match int_legs__team_from_players int_legs__team_match int_player__page_profile
  int_player_club_season__metrics int_player_competition_benchmark_metrics_long
  int_player_competition_benchmarks int_player_match__metrics int_player_momentum__metrics
  int_player_page__window_seasons int_player_profile__contribution int_player_profile__yoy
  int_player_season__metrics int_player_season__team int_player_season_position__metrics
  int_player_season_record int_player_squad_window__metrics int_player_window__metrics
  int_standings__official_rank int_standings__section_kinds int_team__current_national_competitions
  int_team_competition_benchmark_metrics_long int_team_competition_benchmarks
  int_team_momentum__metrics int_team_momentum_window int_team_profile__streaks int_team_profile__yoy
  int_team_season__biggest_results int_team_season__deserved_vs_actual int_team_season__longest_runs
  int_team_season__metrics int_team_season__metrics_cumulative int_team_season__standings_primary
  int_team_season__table_by_time int_team_season__table_legs int_team_season__table_state
  int_team_season_record mart_competition_fixtures mart_competition_index
  mart_competition_season_summary mart_fixture_standing_context mart_head_to_head mart_leaderboards
  mart_match_days mart_matchday_insights mart_next_matchday mart_player_career
  mart_player_competition_benchmarks mart_player_fixture_stats mart_player_momentum
  mart_player_profile mart_player_season_record mart_player_squad_benchmarks
  mart_player_window_metrics mart_roster mart_standings mart_team_competition_benchmarks
  mart_team_competitions mart_team_fixtures mart_team_index mart_team_leaderboards
  mart_team_momentum_window mart_team_profile mart_team_season mart_team_season_insights
  mart_team_season_record mart_team_window_metrics.
  consumption: scripts/export_site_data.py reads only the marts dataset. Competition slug, name,
  confederation and tier come from mart_competition_index; the home boards' pool from
  competition_group on mart_leaderboards and mart_team_leaderboards; season labels from
  mart_team_profile and mart_competition_fixtures; fixture team countries from
  mart_competition_fixtures; top-player names and photos from mart_player_season_record; standings
  team slugs from mart_standings; the Teams page's region rank and label key from mart_team_index.
  Prod measured 2026-11-09: every fixture league_code is in mart_competition_index, every
  standings season has fixtures, one standings team has no fixture (hence mart_standings.team_slug).
  ci_layer_rules: scripts/check_layer_contract.py (gains the seed-reader and marts-only export
  rules), scripts/check_registry_var_sync.py, scripts/check_description_hygiene.py,
  scripts/check_relationships_coverage.py.
  deploy_order: one merge; the nightly loads the seeds and rebuilds every model before the export
  reads the marts. No backfill.
  blast_radius: no value changes. dim_league, dim_competition_season and seven marts gain columns;
  every other changed model reads the same values from a dim that it read from a seed, checked by
  comparing each changed model with prod both ways in the MR build. Exported payloads keep their
  content; competitions.json lists its keys in league_code order, and leaderboards/*.json (read by
  no page) carries the warehouse competition name.

approved_design:
  - none: no page output changes

decisions_taken: >
  The revised plan on #83, approved in chat 2026-11-09: fixed facts on dim_league, tier and
  competition_group per season on dim_competition_season from competition_season_map with
  carry-forward, both removed from the registry; build_nav orders by mart_competition_index.tier,
  then the YAML's sort_order; the export reads marts only. The two layering.md lines are the text
  approved in chat, 2026-11-09. The CI rules extend the existing check_layer_contract.py, approved
  in the same plan. No new mechanism and no recurring cost: dry runs on #83 put the nightly change
  at about zero.

decisions_reserved:
  - Whether nav.json and build_nav are removed (no page reads nav.json).
  - How the home pool rotates between groups (#101).
  - Whether sort_order leaves the registry (only build_nav reads it).

acceptance_criteria:
  - One core table publishes every competition fact that is fixed for a competition, one row per competition: type, club or national, parent competition, confederation, slug and season type.
  - The competition-season table publishes each season's tier and group, from the per-season map, a blank season taking the previous season's value.
  - The registry no longer holds tier or group.
  - Keys are tested unique and not null, and a competition with a blank type fails the build.
  - No model or dbt test reads the `competition_registry` seed except dim_league, and a CI check fails any new reader.
  - The export reads only the marts dataset, and a CI check fails any other read.
  - Every page's exported data is unchanged.

done_when:
  - dbt parse succeeds from the repo root.
  - python scripts/check_layer_contract.py passes, and fails on a planted seed reader and a planted core read in the export (pytest).
  - python -m pytest tests -q is green.
  - SQLFluff lint adds no violation on any changed model.
  - The offline gates in FAST_GATES pass.
  - CI's data:build:mr is green, and every changed model equals prod both ways.

amendments:
  - 2026-11-09: the four relationship tests in dbt_project/seeds/schema.yml that pointed at the competition_registry seed point at dim_league, and check_layer_contract.py scans every dbt_project file except target, dbt_packages and logs, with no exemption; authority: acceptance criterion 5 and the layering.md line approved in chat, 2026-11-09, applied as written.
