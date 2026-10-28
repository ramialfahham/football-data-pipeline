# Verification — the Team page's recent matches and last season's position

Checked locally on the branch: dbt parse; SQLFluff on every changed model and the two new tests
(clean); a dry run of each changed model and of the new and changed tests against prod (valid,
0.1 to 413.3 MiB each if run); the six offline gates; pytest (1,612 passed, 2 skipped). The MR's
data build runs the models and their tests in BigQuery.

Lineage: `dbt ls --select int_team_momentum_window+ int_standings__section_kinds+
int_team_season__position_by_match+ --resource-type model` lists 14 models, the ones the contract's
impact map names.

criteria_demonstrated:
  - int_team_momentum_window adds a team window per team with a finished match: upcoming_fixture_sk NULL, window_type last_5, the last five finished matches before now within its entity type, a club's within the season of its latest finished match; assert_team_window_holds_the_last_five recomputes it from int_legs__team_match; int_team_momentum__metrics, int_player_momentum__metrics and the two formula tests filter upcoming_fixture_sk is not null, and the coverage and form-rule tests join on the upcoming fixture, so they leave the rows out.
  - mart_team_momentum_window left-joins the upcoming fixture, so the team window's rows are listed with league_code and is_home NULL; the not_null tests on those two columns apply where upcoming_fixture_sk is set, and team_momentum_window_team_window_is_a_last_5 pins the team window's shape; assert_momentum_window_matches_momentum compares the fixture windows only.
  - int_standings__section_kinds holds the section-kind resolution mart_standings had inline, every section name with its kind (league where no pattern matches), tested unique and to the five kinds; mart_standings reads it and keeps its coalesce; the row-for-row comparison with prod runs after the MR data build.
  - int_team_season__position_by_match ranks by rank() over points, goal difference and goals within the league-season, section and match number, for domestic-league seasons with no split round and one section per team; tested for the grain and a place of 1 or more; assert_team_position_by_match_matches_final_table warns and stores each team whose rank at the official table's played count differs from the official rank.
  - int_team_profile__yoy serves points_rank_prev_season, the rank at the previous season's row of the same cutoff, and mart_team_profile carries it, described by the generated points_rank_prev_season__team block; team_profile_yoy_points_rank_is_a_place tests it is 1 or more and empty where games_played_prev is.
  - metric_catalogue.csv holds points_rank (team, model, integer, lower_better); sync_metric_docs_blocks.py wrote its two blocks and its metric-map row, and --check passes; rule R7 names it. The generator's `_prev_season` phrase is split into two sentences with its words unchanged, so metric_columns.md holds 15 long sentences, and the pin in test_sentence_length_in_docs.py is 15.
  - The team payload carries recent_matches, the team window's rows by recency_rank without the window's keys; test_the_team_payload_lists_its_recent_matches_newest_first and test_a_sampled_team_export_reads_the_team_window_of_the_sample pin it.
