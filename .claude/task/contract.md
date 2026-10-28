# Task contract — the Team page's recent matches and last season's position

objective: >
  The warehouse serves two more values of the Team page (#235, design #134). Recent matches: every
  team also has a team window in int_team_momentum_window, its last five finished matches
  (cross-competition within its entity type, a club's in the season of its latest match), so
  mart_team_momentum_window lists them for a team with or without a next match, and before a new
  season starts. Position and points: last season's position at the same number of matches, on
  mart_team_profile, ranked by points, then goal difference, then goals scored within the team's
  table section of last season, and tested against the official final table. That position is a
  computed metric, so it enters the catalogue as points_rank and rule R7 names it.

refs: >
  #235 (the build; its plan approved in chat, 2026-10-28, with the decision "rank last season's
  teams at the same number of matches by points, then goal difference, then goals scored; the
  warehouse tests it against the official final table"); #134 (the Team page design, approved in
  chat, 2026-10-22 and 2026-10-28: Recent matches is the match page's block and mart, a team with
  no next match still served its last five; before a new season's first match Recent matches shows
  the season just finished; Position and points shows "Season before: {value}", the season before
  at the same point). The points_rank catalogue row, rule R7's new text and the column name
  points_rank_prev_season: approved in chat, 2026-10-28.

scope_paths:
  - dbt_project/models/4_intermediate/shared/int_team_momentum_window.sql
  - dbt_project/models/4_intermediate/shared/int_momentum_window.yml
  - dbt_project/models/4_intermediate/shared/int_team_momentum__metrics.sql
  - dbt_project/models/4_intermediate/shared/int_player_momentum__metrics.sql
  - dbt_project/models/4_intermediate/shared/int_momentum.yml
  - dbt_project/models/4_intermediate/shared/int_standings__section_kinds.sql
  - dbt_project/models/4_intermediate/shared/int_standings__section_kinds.yml
  - dbt_project/models/4_intermediate/shared/int_team_profile__yoy.sql
  - dbt_project/models/4_intermediate/shared/*.yml
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season__position_by_match.sql
  - dbt_project/models/4_intermediate/domestic_league/team_season/*.yml
  - dbt_project/models/5_marts/shared/mart_team_momentum_window.sql
  - dbt_project/models/5_marts/shared/mart_standings.sql
  - dbt_project/models/5_marts/shared/mart_team_profile.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/models/docs/*.md
  - dbt_project/seeds/metric_catalogue.csv
  - dbt_project/seeds/metric_map.csv
  - dbt_project/tests/assert_*.sql
  - scripts/export_site_data.py
  - scripts/sync_metric_docs_blocks.py
  - tests/test_export_site_data.py
  - tests/test_sentence_length_in_docs.py
  - tests/test_no_decision_history_in_code.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md

impact_map: >
  writers: int_team_momentum_window gains the team-window rows (upcoming_fixture_sk empty);
  int_team_momentum__metrics and int_player_momentum__metrics leave them out, so the form
  aggregates and every mart built on them are unchanged; mart_team_momentum_window lists them.
  A new intermediate int_standings__section_kinds holds the section-kind resolution mart_standings
  does today, and mart_standings reads it unchanged in output. A new intermediate
  int_team_season__position_by_match ranks each domestic league-season's teams at every match
  number; int_team_profile__yoy and mart_team_profile carry points_rank_prev_season. downstream:
  `dbt ls --select int_team_momentum_window+ int_standings__section_kinds+
  int_team_season__position_by_match+ --resource-type model` lists 14 models: the six changed or
  new intermediates, mart_standings, mart_team_momentum_window and mart_team_profile, and
  mart_fixture_standing_context, mart_matchday_insights, mart_player_momentum,
  mart_team_competitions and mart_team_window_metrics, whose output is unchanged since their
  inputs leave out the team window or are row for row the same. The export's team payload
  gains the recent-matches rows. layer_rules: the selection and the ranking are computed in the
  warehouse; the export only selects. The catalogue gains one model-computed row, points_rank, and
  its generated docs block and metric-map row; rule R7 names it. deploy_order: the MR data build;
  the committed samples are re-exported with the page's build. blast_radius: the window's new rows
  and the readers that leave them out, the two new intermediates, one new profile column, one
  catalogue row, the team payload's new key.

approved_design:
  - team: #134

acceptance_criteria:
  - "int_team_momentum_window has, for every team with a finished match, a team window: upcoming_fixture_sk empty, window_type last_5, its last five finished matches before now within its entity type, a club's in the season of its latest finished match, recency_rank 1 to 5; a test recomputes it from int_legs__team_match; int_team_momentum__metrics, int_player_momentum__metrics and the form tests leave those rows out, so their output is unchanged."
  - "mart_team_momentum_window lists the team window's rows with upcoming_fixture_sk empty, the played match's competition, round, score, result and opponent; its grain tests hold."
  - "int_standings__section_kinds resolves each standings section name to its table kind exactly as mart_standings did, and mart_standings reads it; after the MR data build a query compares the MR's mart_standings with prod's, row for row."
  - "int_team_season__position_by_match ranks each domestic league-season's teams at every match number by points, then goal difference, then goals scored (rank, so equal teams share a place), within the team's section of that season's official table, where every team sits in one section that is a league, conference or group table; a split season has no rank. A warning test with stored failures compares the rank at the final table's matches played with the official final rank."
  - "int_team_profile__yoy and mart_team_profile carry points_rank_prev_season: the rank last season at the match number of the points_prev_season row; empty where that season has no rank; tested to be a place of 1 or more, and empty where the previous season is."
  - "metric_catalogue.csv holds points_rank (team, model, integer, lower_better); its docs block and metric-map row are generated; rule R7 says a position at a point the league published no table for is computed as points_rank."
  - "The team payload carries its recent matches, the team window's rows newest first with the display fields only; pytest pins it."

decisions_taken: >
  The build plan approved in chat, 2026-10-28, and #134's notes on Recent matches, the off-season
  page and Position and points. Readings: the team window is anchored now, not at a next fixture,
  so it is the same before, during and after a season, and a club's window holds the season of its
  latest finished match, which is the season the page shows; the team window is a last_5 window,
  so no window type is added; last season's position ranks within the team's own section of last
  season's table (an MLS conference), since a position in another table compares unlike numbers;
  a season split into rounds or with a team in two sections (Liga MX's Apertura and Clausura, a
  championship and relegation round) has no position at the same point, and the page shows its
  "Season before: –"; points are counted from the results, so a points deduction the official
  table carries is a difference the warning test lists. No new dependency; the recurring cost is
  measured on the MR data build and put to the CPO before the merge.

decisions_reserved:
  - Any wording, block or rule the Team page design does not hold; the squad's appearances follow in their own MR.

done_when:
  - dbt parse, SQLFluff on every changed model, a dry run of each against prod, pytest and the offline gates pass.
  - The MR data build passes, including the new tests; its added bytes are measured and put to the CPO.
  - Reviewers per review_routing.json pass.

amendments: >
  Round 1 of the warehouse review found the computed position outside the catalogue, against rule
  R7. The points_rank row, R7's new text and the column name points_rank_prev_season were approved
  in chat, 2026-10-28, and enter scope with metric_catalogue.csv and metric_map.csv; the
  football-analytics reviewer runs on the row. The generated `_prev_season` phrase is one sentence
  over 25 words, and the new column's block would add a copy to a document whose count may only
  fall. The phrase is split into two sentences with its words unchanged, and the pin drops to the
  new count.
