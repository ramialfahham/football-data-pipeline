# Task contract — shoot-out points and last season's position for a season of two tournaments

objective: >
  Two errors in last season's position on the Team page (#235). A league match drawn and then
  decided by a shoot-out gives the shoot-out winner 2 points (J1 2026 awarded them; the warehouse
  counted 1), through a new team-leg column and the catalogue formulas of points_won and
  points_capture_pct. A season whose results do not reproduce its official table through the
  table's matches played (Argentina 2025: an Apertura and a Clausura, the stored table only the
  Clausura) has no position, and a position is ranked only up to the table's matches played.

refs: >
  #235 (the Team page build). Approved in chat, 2026-10-28, with the fix plan: one MR for both
  fixes; rule R3's sentence "A league match level at full time and decided by a shoot-out gives the
  shoot-out winner 2 points and the loser 1."; points_won's description "Points the team won: 3 for
  a win, 1 for a draw, none for a defeat. A league match drawn and then decided by a shoot-out gives
  the shoot-out winner 2." and interpretation "Points tally in the window (3 per win / 1 per draw /
  0 per loss; 2 for a league shoot-out win)"; and the formulas of points_won and points_capture_pct
  counting a table shoot-out win as 2 points, written sum(case result when 'W' then 3 when 'D' then
  1 else 0 end) + countif(is_table_shootout_win), with points_capture_pct's denominator and
  description unchanged. The approved split-season rule (a season split into rounds shows "Season
  before: –") is #134's and the build plan's.

scope_paths:
  - dbt_project/models/4_intermediate/shared/int_legs__team_match.sql
  - dbt_project/models/4_intermediate/shared/int_legs.yml
  - dbt_project/models/4_intermediate/shared/int_team_season_record.sql
  - dbt_project/models/4_intermediate/shared/int_team_momentum_window.sql
  - dbt_project/models/4_intermediate/shared/int_team_momentum__metrics.sql
  - dbt_project/models/4_intermediate/shared/*.yml
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season__metrics_cumulative.sql
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season__position_by_match.sql
  - dbt_project/models/4_intermediate/domestic_league/team_season/*.yml
  - dbt_project/models/docs/*.md
  - dbt_project/seeds/metric_catalogue.csv
  - dbt_project/seeds/metric_map.csv
  - dbt_project/tests/assert_*.sql
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md

impact_map: >
  writers: int_legs__team_match gains is_table_shootout_win; int_team_season_record and
  int_team_momentum_window carry it; the generated points_won and points_capture_pct in
  int_team_season__metrics_cumulative and int_team_momentum__metrics count a table shoot-out win
  as 2 points; int_team_season__position_by_match keeps a season only where the results reproduce
  the official table and ranks up to its matches played. downstream: the readers of those models
  (listed by dbt ls in the evidence); values change only for teams with a shoot-out in a table
  round and for the seasons the new check leaves out. layer_rules: computed in the warehouse;
  no export change. deploy_order: the MR data build. blast_radius: one leg column, two catalogue
  formulas and one description, the ranking's season filter.

approved_design:
  - team: #134

acceptance_criteria:
  - "int_legs__team_match carries is_table_shootout_win: TRUE where the match is in a table round, finished on penalties and the team won the shoot-out; FALSE otherwise; tested not null and to be a draw; int_team_season_record and int_team_momentum_window carry it."
  - "assert_team_season_equals_league_table compares our points with the table's points plus the points taken; a new warning test with stored rows compares every ranked team's points at the table's matches played with the same, and after the MR data build it holds no J1 2026 row."
  - "points_won and points_capture_pct in metric_catalogue.csv count a table shoot-out win as 2 points; points_won's description and interpretation carry the approved text; generate_metric_sql.py --check and sync_metric_docs_blocks.py --check pass; rule R3 carries the approved sentence."
  - "int_team_season__position_by_match ranks a season only where every team's goals scored and conceded through the official table's matches played equal the table's, and only up to the table's matches played; after the MR data build the final-table warning lists no Argentina 2025 row and no J1 2026 team whose points differ."

decisions_taken: >
  The R3 sentence, the points_won description and interpretation, and one MR: approved in chat,
  2026-10-28. Readings: a league match is a match in a table round by int_round_names, so a cup or
  play-off shoot-out stays a draw worth 1; a season the results do not reproduce is the approved
  split-season case and shows no position. Points deductions and other tie-break rules are not
  changed here. No new dependency; the recurring cost is measured on the MR data build and put to
  the CPO before the merge.

decisions_reserved:
  - Points deductions in last season's position.

done_when:
  - dbt parse, SQLFluff on every changed model, a dry run of each against prod, pytest and the offline gates pass.
  - The MR data build passes; its added bytes are measured and put to the CPO.
  - Reviewers per review_routing.json pass.

amendments: >
  Round 1 of the warehouse review: the league-table test still expected 3 x wins + draws, the
  shoot-out flag had no test that it is a draw, the new points had no value test, and refs did not
  quote the approved texts or name points_capture_pct. The test, the draw test, the value test and
  the quotes are added.
