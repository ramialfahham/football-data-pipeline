# Verification — shoot-out points and last season's position for a season of two tournaments

Checked locally on the branch: dbt parse; generate_metric_sql.py --check and
sync_metric_docs_blocks.py --check; SQLFluff on every changed model (clean) and on the changed yoy
test (four findings, the same four main has, none on the changed line); a dry run of each changed
model and of the three tests that read them against prod (valid, 2.1 to 29.4 MiB each if run);
the six offline gates; pytest (1,612 passed, 2 skipped). The MR's data build runs the models and
their tests in BigQuery.

Lineage: `dbt ls --select int_legs__team_match+ --resource-type model` lists 44 models. Their
values change only for a team with a shoot-out in a table round (J1 2026 in the data today) and
for the seasons the ranking's new check leaves out. The 5.5 MB prod query behind the fix: J1 2026
East and West hold 270 points each over 90 matches, 51 of them level; Argentina 2025's stored
table is the Clausura's two zones at 16 played, while each team played 16 Apertura and 16 Clausura
table matches and the knockout rounds.

criteria_demonstrated:
  - int_legs__team_match carries is_table_shootout_win from int_round_names' round_stage_kind table, status PEN and fct_fixture's winner, coalesced to FALSE; tested not null there and on int_team_season_record and int_team_momentum_window, which carry it; legs_table_shootout_win_is_a_draw fails a shoot-out win whose result is not a draw.
  - assert_team_season_equals_league_table compares points_won with the table's points plus the points taken, which with its wins, draws and losses checks covers the two lines it replaces; assert_team_position_points_equal_the_table (warn, stored rows) compares every ranked team's points at the table's matches played the same way; its J1 2026 rows are read after the MR data build. Both and the draw test dry-run valid against prod (2.1, 9.5 and 7.1 MiB).
  - points_won and points_capture_pct are sum(case result when 'W' then 3 when 'D' then 1 else 0 end) + countif(is_table_shootout_win) in metric_catalogue.csv; points_won carries the approved description and interpretation; the generator rewrote int_team_season__metrics_cumulative and int_team_momentum__metrics and both checks pass; R3 carries the approved sentence; assert_team_yoy_pairs_the_same_games_played adds the shoot-out point.
  - int_team_season__position_by_match keeps a season only where every team's goals scored and conceded at the table's matches played equal the table's (a team with no row there fails it), and ranks only up to each team's table matches played; the Argentina 2025 and J1 2026 counts in the final-table warning are read after the MR data build.
