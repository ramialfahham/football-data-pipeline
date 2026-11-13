# Task contract — two rounds under one name, and season labels by edition

objective: >
  Issues #278 and #258, batch E2 of the #290 data defects. A knockout round that the provider files
  under another round's name takes its own round, from a sourced per-fixture correction applied in
  base, so a team shows each tie once under its own round. A season's label follows the edition's
  season_type in competition_season_map, so J1 2027 reads 2026/27, the CONCACAF Champions Cup
  2018–2026 and the AFC Champions League 2016–2022 read as one year, and the UEFA Super Cup stays
  one year.

refs: >
  #278, #258, #290. Batch E2 and the UEFA Super Cup ruling (the map row stays one year) approved in
  chat, 2026-11-12, through the coordinating session. #278's plan approved in chat, 2026-11-09.

scope_paths:
  - .claude/task/290-e2-rounds-season-labels/
  - dbt_project/seeds/fixture_round_corrections.csv
  - dbt_project/seeds/round_names.csv
  - dbt_project/seeds/competition_season_map.csv
  - dbt_project/seeds/schema.yml
  - dbt_project/models/2_base/api_football/base_apif__fixtures_next.sql
  - dbt_project/models/2_base/api_football/base.yml
  - dbt_project/models/3_core/dim_competition_season.sql
  - dbt_project/models/3_core/core.yml
  - dbt_project/models/4_intermediate/shared/int_knockout_ties.yml
  - dbt_project/models/4_intermediate/shared/int_team_index__round_values.sql
  - dbt_project/models/docs/shared_columns.md
  - dbt_project/tests/assert_result_corrections_applied.sql
  - dbt_project/tests/assert_season_label_answer_key.sql
  - site_v2/src/i18n/strings.ts

impact_map: >
  writers: base_apif__fixtures_next is the only writer of a fixture's round_name; fct_fixture reads
  it, and every round reader reads fct_fixture (int_round_names, int_knockout_ties, int_legs__*,
  the team-season models, mart_competition_fixtures, mart_next_matchday, mart_team_competitions,
  mart_team_fixtures, mart_team_index and others). round_names is read only by int_round_names.
  A round's copy key is also a key of int_team_index__round_values, the Teams page's points per
  reached round, which mart_team_index joins on reached_round_label_i18n_key and
  assert_team_index_cup_rounds_scored checks for every counted top-cup round: the two new keys
  take 0 points there, as every other preliminary and qualifying round does. The shared
  round_name description in docs/shared_columns.md names the corrected round too.
  dim_competition_season is the only writer of season_label; competition_season_map is read by
  dim_competition_season, int_competition_season__club_windows (through dim_competition_season)
  and the tests assert_player_has_page and assert_season_map_covers_club_editions.
  downstream: `dbt ls --select base_apif__fixtures_next+ round_names+ --resource-type model`
  (run 2026-11-12) gives 93 models, 33 of them marts. `dbt ls --select dim_competition_season+
  competition_season_map+ --resource-type model` gives 39 models, 23 marts:
  mart_competition_fixtures mart_competition_index mart_fixture_standing_context mart_leaderboards
  mart_match_days mart_matchday_insights mart_next_matchday mart_player_competition_benchmarks
  mart_player_fixture_stats mart_player_index mart_player_profile mart_player_squad_benchmarks
  mart_player_window_metrics mart_roster mart_standings mart_team_competitions mart_team_index
  mart_team_leaderboards mart_team_momentum_window mart_team_page_window_metrics mart_team_profile
  mart_team_season mart_team_season_insights. season_label is a display column in each: no model
  joins, groups or filters on it (grep of dbt_project/models), and the export reads it as text.
  The UESC map rows change season_type only; their split_year_season and calendar_year_season are
  equal on every row, so as a member of a window each edition reads the same year. As an anchor,
  int_competition_season__club_windows reads the anchor's own season_type: one player's featured
  season on prod is UESC 2026 (2.9 MB query, 2026-11-12), and no team's (150 MB). As a
  calendar-year anchor its window also admits the 2026 editions of calendar-year leagues, but
  that player's only club match since 2024 is the UESC 2026 match itself (97 MB), so his windows
  hold the same matches; the ci_mr comparison checks it.
  layer_rules: the correction is a seed applied in base, beside fixture_result_corrections. No
  per-competition model, no partition_by or cluster_by. The label rule names no league_code.
  deploy_order: additive seed rows and a column rule in base and core. The merge rebuilds
  everything downstream in data:build:main; nothing reads a column this removes.
  blast_radius: measured on prod, 2026-11-12. Rounds: 44 fixtures change round (32 CAF Champions
  League 2025 fixtures of 17 October to 1 November, 16 ties, to "2nd Preliminary Round"; 12 UCL fixtures of
  2019, 2021, 2022 and 2023 to "Preliminary Round - Semi-finals" or "Preliminary Round - Final").
  The new round_names rows also name UCL 2018's three preliminary fixtures, which the provider
  already files under those texts and which today resolve to no round. 37 team-rounds of
  int_knockout_ties lose their second tie; mart_team_competitions' reached round changes for the
  teams in those ties. Labels: 18 season labels change (AFCCL 7, CCCU 10, J1 1); the MR head
  lists each one before and after.

approved_design:
  - competition: #129
  - matches: #130
  - team: #134

acceptance_criteria:
  - On the English, German and Finnish pages, a round named by the copy key roundPreliminarySemiFinals reads "Preliminary round · Semi-finals", "Vorrunde, Halbfinale" and "Esikarsinta, välierät".
  - On the English, German and Finnish pages, a round named by the copy key roundPreliminaryFinal reads "Preliminary round · Final", "Vorrunde, Finale" and "Esikarsinta, finaali".
  - Every round key that int_round_names serves for a UCL 2019, 2021, 2022 or 2023 preliminary fixture, or a CAF Champions League 2025 preliminary fixture, has a string in all three languages.

decisions_taken: >
  The mechanism follows #278's plan: rounds the provider gives one name are named apart by a
  correction seed. fixture_round_corrections is a correction seed of the existing kind (one row
  per fixture, a source on every row), applied in base_apif__fixtures_next as
  fixture_result_corrections is; assert_result_corrections_applied checks it is applied, sourced
  and still needed. No new mechanism.
  Each corrected round text is one the provider itself uses: "2nd Preliminary Round" (CAF
  Champions League, named by the existing CAFCL round_names row), and "Preliminary Round -
  Semi-finals" and "Preliminary Round - Final" (UCL 2018 in the provider's own feed). Which
  fixtures belong to which round follows the organiser's published draw and results (CAF, UEFA).
  The preliminary semi-finals and final are rounds of knockout ties (stage_kind knockout); the
  competition's final stays the only stage_kind final.
  The season label takes its kind from the edition's competition_season_map row, as #258 says:
  split_year names split_year_season and the next year (2026/27); calendar_year names
  season_api_year, which keeps tournament names as they are (AFCON 2023, Club World Cup 2025). An
  edition the map does not hold keeps the competition's season_type from dim_league. The UEFA
  Super Cup's map rows become calendar_year, so it stays one year (ruled in chat, 2026-11-12,
  through the coordinating session).
  The old test that a label starts with the provider's year is replaced: J1 2027 and the CONCACAF
  Champions Cup 2017 correctly start with the year before. Its successor checks the label's form
  against the map, and an answer-key test pins named editions to their published names.
  A team holds at most one tie per round: a uniqueness test on int_knockout_ties over (league,
  season, round, team). It fails on prod today on the 37 team-rounds.

  The EN, DE and FI wording of the two new round labels (roundPreliminarySemiFinals,
  roundPreliminaryFinal) and the acceptance criteria that state it: approved in chat, 2026-11-12,
  through the coordinating session.

decisions_reserved:
  - none: the only open question, the wording of the two round labels, is answered above.

done_when:
  - dbt parse passes; SQLFluff passes on every changed model and test; the offline gates and the
    full pytest pass.
  - The changed base_apif__fixtures_next and dim_competition_season, compiled and run read-only on
    prod, carry every corrected round and every label in the answer key.
  - On the MR's ci_mr tables, the int_knockout_ties uniqueness test, assert_result_corrections_applied
    and assert_season_label_answer_key return no rows; compared with prod, only the listed fixtures'
    rounds and the listed labels change.

amendments: (none)
