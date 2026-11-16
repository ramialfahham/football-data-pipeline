# Task contract — a keeper's save percentage leaves out the own goals conceded while he was in goal

objective: >
  Issue 184: a keeper's save percentage is saves / (saves + goals conceded while he was in goal
  that were not own goals), wherever it is computed. A new per-match atom, goals_own_against on
  the player legs, carries the own goals the team conceded while the player was on the pitch; the
  catalogue denominators of saves_player_pct and shots_on_goal_against_player subtract it, and the
  generated metric SQL follows.

refs: >
  Issue 184, one of the go-live gate items in issue 290. Team save percentage, issue 180, is the
  same fix at team grain and is reused, not repeated.

scope_paths:
  - dbt_project/models/2_base/api_football/base_apif__fixture_players.sql
  - dbt_project/models/2_base/api_football/base_apif__fixture_players_from_lineups.sql
  - dbt_project/models/3_core/fct_fixture_player_stats.sql
  - dbt_project/models/3_core/core.yml
  - dbt_project/models/4_intermediate/shared/int_legs__player_match.sql
  - dbt_project/models/4_intermediate/shared/int_legs.yml
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_player_season__metrics.sql
  - dbt_project/models/4_intermediate/shared/int_player_momentum__metrics.sql
  - dbt_project/models/4_intermediate/shared/int_player_season_position__metrics.sql
  - dbt_project/models/4_intermediate/shared/int_player_season_record.sql
  - dbt_project/models/4_intermediate/shared/int_player_squad_window__metrics.sql
  - dbt_project/models/4_intermediate/shared/int_player_window__metrics.sql
  - dbt_project/macros/player_benchmark_metrics.sql
  - scripts/generate_metric_sql.py
  - dbt_project/models/4_intermediate/shared/int_player_season_position.yml
  - dbt_project/models/4_intermediate/shared/int_player_page.yml
  - dbt_project/seeds/metric_catalogue.csv
  - dbt_project/models/docs/metric_columns.md
  - dbt_project/tests/assert_keeper_save_pct_leaves_out_own_goals.sql
  - .claude/task/184-save-pct-own-goals/contract.md
  - .claude/task/184-save-pct-own-goals/review.md
  - .claude/task/184-save-pct-own-goals/review_input.patch

impact_map: >
  writers: base_apif__fixture_players and base_apif__fixture_players_from_lineups, unioned by
  fct_fixture_player_stats, read by int_legs__player_match. No raw table, loader or seed other
  than metric_catalogue.csv changes.
  downstream: `dbt ls --select base_apif__fixture_players+ base_apif__fixture_players_from_lineups+
  --resource-type model` lists base_apif__lineup_sheets base_apif__lineups base_apif__players
  dim_player fct_fixture_lineup fct_fixture_player_stats
  int_competition_season__player_stat_corrections int_legs__player_match
  int_legs__team_from_players int_player__national_team_minutes int_player__page_profile
  int_player_club_season__metrics int_player_competition_benchmark_metrics_long
  int_player_competition_benchmarks int_player_match__metrics int_player_momentum__metrics
  int_player_page__window_seasons int_player_profile__contribution int_player_profile__yoy
  int_player_season__metrics int_player_season__team int_player_season_position__metrics
  int_player_season_record int_player_squad_window__metrics int_player_window__metrics
  int_team__current_national_competitions int_team__featured_season
  int_team_competition_benchmark_metrics_long int_team_competition_benchmarks
  int_team_competition_phase__metrics int_team_momentum__metrics int_team_profile__yoy
  int_team_season__deserved_vs_actual int_team_season__metrics
  int_team_season__metrics_cumulative int_team_season_record int_team_window__metrics
  mart_competition_fixtures mart_leaderboards mart_match_days mart_matchday_insights
  mart_player_career mart_player_competition_benchmarks mart_player_fixture_stats
  mart_player_index mart_player_momentum mart_player_profile mart_player_season_record
  mart_player_squad_benchmarks mart_player_window_metrics mart_roster
  mart_team_competition_benchmarks mart_team_competitions mart_team_index mart_team_leaderboards
  mart_team_momentum_window mart_team_page_window_metrics mart_team_profile mart_team_season
  mart_team_season_insights mart_team_season_record mart_team_window_metrics. Only the player
  metric surfaces read the new column; every other model is unchanged in value.
  layer_rules: the keeper spell is cleaning logic and stays in base, next to the spell logic that
  already fills goals_against; core and the legs only carry the column; the formula lives in the
  catalogue and is written into the models by scripts/generate_metric_sql.py.
  deploy_order: a column added at base and carried down; the nightly's full build rebuilds every
  layer in order, so nothing breaks between merge and the next 04:00 run.
  blast_radius: saves_player_pct and shots_on_goal_against_player change only for a keeper whose
  window holds a match where he conceded an own goal, or whose own goals conceded are unknown
  (the value is then NULL, as every other metric with a missing input). The saves_player_pct
  leaderboard floor (shots_on_goal_against_player) may drop a keeper below it. The before and
  after list comes from data:build:mr's ci_mr tables against prod.

approved_design:
  - none: no page output changes; the save percentage block shows the same metrics with corrected values

depends_on:
  - none: the change starts from gitlab/main at 70eec4c7; no open MR carries code it needs
shared_files:
  - none: no design baseline, chart manifest or chart pin changes

decisions_taken: >
  The atom reuses the keeper spell base_apif__fixture_players and the lineup-built rows already
  derive to fill goals_against (the substitution and red-card minutes): the own goals counted are
  the opponent-credited own goal events inside the spell. A keeper with no change in a match where
  he was his team's only keeper with minutes was in goal throughout, and takes every own goal his
  team conceded, counted from the events only where the conceded goal events add up to the goals
  conceded: the rule base_apif__fixture_statistics applies to the own goals team save percentage
  uses (issue 180). A
  spell is trusted only when the conceded goal events add up to the goals conceded and no goal
  fell at a change minute, the guard goals_against already uses. goals_against = 0 means no own
  goal conceded. Otherwise the atom is NULL, and so is every rate over a window that holds it
  (catalogue rule R4). The competition benchmark's denominator for saves_player_pct is the
  catalogue's shots_on_goal_against_player, so the position and page-window surfaces generate that
  column too, one definition per rate (engineering_standards.md §3.2), instead of the macro adding
  saves and goals conceded by hand. Engineering calls by the coordinating session. No new mechanism, no
  recurring cost; read-only BigQuery for the value test and the comparison.

  Catalogue descriptions, approved in chat, 16 Nov 2026: saves_player_pct reads "The player's saves
  as a share of the player's saves plus the goals conceded while the player was in goal. Own goals
  are not counted." and shots_on_goal_against_player, changed in the same MR, reads "Shots on
  target the player faced in goal: the player's saves plus the goals conceded while the player was
  in goal. Own goals are not counted." Labels and metric ids are unchanged.

decisions_reserved:
  - none: the two catalogue descriptions are approved as quoted above; nothing else a fan reads changes in wording.

done_when:
  - python scripts/generate_metric_sql.py --check passes; the catalogue denominators read sum(saves + goals_against - goals_own_against).
  - Full pytest, dbt parse and sqlfluff lint green via python scripts/ci_local.py --mr.
  - data:build:mr green, including assert_keeper_save_pct_leaves_out_own_goals on a real match with an own goal and assert_player_metrics_follow_catalogue_formula.
  - A read-only comparison of the MR's ci_mr tables against prod lists every keeper whose saves_player_pct changed, and why, on the MR.

amendments: (none)
