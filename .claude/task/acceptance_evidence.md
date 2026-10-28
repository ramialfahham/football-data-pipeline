# Verification — the Team page's comparison data, cards and highs and lows

Checked locally on the branch: dbt parse; SQLFluff on every changed model and the two new tests
(clean, mart_team_competition_benchmarks and mart_team_profile showing only main's dbt_utils
baseline); a dry run of each changed model and the two new tests against prod, with this branch's
models inlined (all valid, 4.9 to 32.9 MB each if run); generate_metric_sql.py --check and
sync_metric_docs_blocks.py --check (the metric map regenerated); the six offline gates; pytest
(1,608 passed, 2 skipped, the relationship-coverage gate included).
The MR's data build runs the models and their tests in BigQuery.

criteria_demonstrated:
  - int_team_competition_benchmark_metrics_long unpivots the 34 metrics of metric_rows.json plus the two the old set held beyond them, the shots-on-target difference and the clean-sheet share (36), counts cast to FLOAT64; the accepted_values lists in both YAML blocks hold the 36. mart_team_competition_benchmarks ranks with `if(direction = 'lower_better', value, -value) asc` from the catalogue's team rows; assert_team_benchmark_rank_follows_direction fails a league-season whose rank 1 is not the best value by direction.
  - The long model reads each team-season's previous domestic season from int_team_season__metrics_cumulative at the latest match at or before its own match count, as int_team_profile__yoy does; assert_team_benchmark_prev_season_matches_yoy fails a difference from the year-over-year model on its 16 shared metrics, and a benchmark metric the catalogue does not hold.
  - mart_team_profile gains cards_yellow, cards_red, longest_unbeaten_run, longest_winless_run and the biggest-win and heaviest-defeat columns (fixture, competition, opponent and its name, home or away, goals, kickoff), each described in shared.yml; int_team_season_records.yml tests uniqueness, the null-below-two rule and that a biggest win is a win and a heaviest defeat a defeat. mart_competition_season_summary's team_longest now selects int_team_season__longest_runs' raw lengths, the CTE logic moved unchanged.
  - mart_team_fixtures: is_upcoming is `status_short in ('NS', 'TBD') and date(kickoff_datetime) >= current_date()`.
  - test_shape_team_benchmark_member_carries_mart_columns pins metric_value_prev_season; test_league_strip_lists_every_club_of_the_featured_season_and_flags_self pins league_strip on the featured season only, clubs in team order with the team flagged.
