# Task contract — a team never shows 0 offsides when one of its players was offside

objective: >
  Issue #338: no team-match shows a team offsides count of 0 while a player of that team (by the
  cleaned team id) has an offside above 0 in the match. The Blank rule gets a guard: a blank that
  the other team's line would zero stays blank when a player of the team has an offside, and a
  provider 0 that its players contradict is withheld. The guard reads the player's cleaned
  offsides, the value the player has in base_apif__fixture_players, so a later fetch that corrects
  a player's offside to 0 leaves the team's 0 standing.

refs: "#338; cleaning_rules (Blank rule); #335 (the full-line clause it extends); #339 (listing, not here)"

scope_paths:
  - .claude/task/338-offsides-guard/**
  - dbt_project/models/2_base/api_football/base_apif__fixture_player_lines.sql
  - dbt_project/models/2_base/api_football/base_apif__fixture_players.sql
  - dbt_project/models/2_base/api_football/base_apif__fixture_statistics.sql
  - dbt_project/models/2_base/api_football/base.yml
  - dbt_project/models/docs/cleaning_rules.md
  - dbt_project/tests/assert_team_offsides_zero_has_no_player_offside.sql
  - dbt_project/tests/assert_team_stat_blank_counts_follow_the_blank_rule.sql
  - dbt_project/tests/assert_base_team_stats_cleaned.sql
  - dbt_project/tests/assert_fixture_statistics_from_every_fetch.sql
  - dbt_project/seeds/team_match_cleaning_answer_key.csv

impact_map: >
  writers: base_apif__fixture_statistics (the Blank rule, offsides) and base_apif__fixture_players
  (its first half moves, unchanged, into the new base model base_apif__fixture_player_lines, so
  that the statistics model can read the players' cleaned offsides without a cycle: the players
  model reads the statistics model for its shots fill and its zero fill).
  downstream: output of `dbt ls --select base_apif__fixture_player_lines+ --resource-type model
  --output name`, 87 models (it covers both changed models, since the statistics model reads the new
  one):
  base_apif__fixture_events_checked base_apif__fixture_player_lines base_apif__fixture_players
  base_apif__fixture_players_checked base_apif__fixture_players_from_lineups
  base_apif__fixture_statistics base_apif__lineup_sheets base_apif__lineups base_apif__players
  dim_player fct_fixture_event fct_fixture_lineup fct_fixture_player_stats fct_fixture_team_stats
  int_competition_season__player_stat_corrections int_legs__player_match
  int_legs__team_from_players int_legs__team_match int_pipeline__corrections_no_longer_needed
  int_player__national_team_minutes int_player__page_profile int_player_club_season__metrics
  int_player_competition_benchmark_metrics_long int_player_competition_benchmarks
  int_player_match__metrics int_player_momentum__metrics int_player_page__window_seasons
  int_player_profile__contribution int_player_season__metrics int_player_season__team
  int_player_season_position__metrics int_player_season_record int_player_squad_window__metrics
  int_player_window__metrics int_standings__official_rank int_team__current_national_competitions
  int_team__featured_season int_team_competition_benchmark_metrics_long
  int_team_competition_benchmarks int_team_competition_phase__metrics int_team_momentum__metrics
  int_team_momentum_window int_team_profile__streaks int_team_season__biggest_results
  int_team_season__deserved_vs_actual int_team_season__longest_runs int_team_season__metrics
  int_team_season__metrics_cumulative int_team_season__standings_primary
  int_team_season__table_by_time int_team_season__table_legs int_team_season__table_state
  int_team_season_record int_team_window__metrics mart_competition_fixtures mart_competition_index
  mart_competition_research_list mart_competition_season_summary mart_fixture_standing_context
  mart_head_to_head mart_leaderboards mart_match_days mart_matchday_insights mart_next_matchday
  mart_player_career mart_player_competition_benchmarks mart_player_fixture_stats mart_player_index
  mart_player_momentum mart_player_profile mart_player_season_record mart_player_squad_benchmarks
  mart_player_window_metrics mart_roster mart_standings mart_team_competition_benchmarks
  mart_team_competitions mart_team_fixtures mart_team_index mart_team_leaderboards
  mart_team_momentum_window mart_team_page_window_metrics mart_team_profile mart_team_season
  mart_team_season_insights mart_team_season_record mart_team_window_metrics
  The opponent clause reads the other team's offsides as delivered, so a team's blank is still
  zeroed by the other team's provider 0 even where that 0 is withheld for the other team; no
  prod team-match shows it (the 7 changed rows are the only differences measured).
  A team offsides count that goes from 0 to blank can only change offsides per match and its
  windows and boards for the team-matches measured below. The players model is meant to be row and
  column identical: its offsides fill (offsides_counted or team_offsides = 0) cannot change where a
  player of the match has an offside above 0, which holds in every changed team-match.
  layer_rules: base reads staging and base only; the new model reads no statistics model, so the
  statistics model reads it with no cycle; one table per grain, no per-competition model.
  deploy_order: the nightly rebuilds base and downstream in order; the new table is built before
  both models that read it; no consumer reads a new column.
  blast_radius: measured read-only on prod (base_apif__fixture_statistics against
  base_apif__fixture_players): 7 team-matches have offsides 0 and a player with an offside above
  0: 974184/81, 1035960/3490, 1099022/10137, 1149592/2546, 1149592/3700, 1187488/11, 1629940/2938.
  The new table is one row per player line of a match (about 2 million), a few hundred MB.

approved_design:
  - none: no page output changes by design; a team value that was a wrong 0 shows blank where a value is served

depends_on:
  - none: base models on main alone
shared_files:
  - none: no design, registry, font or chart baseline changes

decisions_taken: >
  A cleaning-rule extension (working_agreement §10, rule extensions): the issue text states it and
  the CPO approves it by merging; the rule sentence stands at the top of the MR head. A model
  split for a dependency cycle is an engineering call: the first half of the players model moves
  without change into its own base model. No new run, dependency or recurring cost beyond one more
  base table. The withheld provider 0 is not recorded in stat_corrections: no consumer reads the
  team entries and listing it for research is #339.

decisions_reserved:
  - none: the rule and its scope are the approved issue text.

done_when:
  - dbt parse and sqlfluff lint of the changed models and tests pass, check_description_hygiene.py and check_layer_contract.py pass.
  - On the MR's ci_mr tables against prod, base_apif__fixture_statistics differs only in offsides of the wrong 0s (0 to blank), every other row and column identical, and base_apif__fixture_players is row and column identical.
  - assert_team_offsides_zero_has_no_player_offside has no exclusion and returns 0 rows; the tests that recompute the Blank rule agree with the rule.
  - python scripts/ci_local.py --mr is green and python scripts/merge_ready.py <MR> says ready.

amendments: (none)
