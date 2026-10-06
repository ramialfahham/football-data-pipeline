# Task contract — no team-season counts fewer games than its competition's standings

objective: >
  The standings games test is red on 3 team-seasons. Declare the Süper Lig match the TFF awarded
  0–3, re-key the two 2021 AFC Champions League standings rows the provider files under the wrong
  club, and make the test an error.

refs: >
  #202. Plan approved by the CPO in chat, 2026-10-05.

acceptance_criteria:
  - Gaziantep FK–Trabzonspor, Süper Lig 19 Mar 2023, counts as awarded 0–3 (TFF board decision, 12 Feb 2023)
  - The 2021 AFC Champions League Group E 2nd place and the best-second-placed ranking belong to Al Wahda FC (UAE), not Al Wehda Club (Saudi Arabia)
  - The standings games test is an error, not a warning, and passes

scope_paths:
  - dbt_project/seeds/fixture_result_corrections.csv
  - dbt_project/seeds/standings_corrections.csv
  - dbt_project/seeds/schema.yml
  - dbt_project/models/2_base/api_football/base_apif__standings.sql
  - dbt_project/models/2_base/api_football/base.yml
  - dbt_project/tests/assert_result_corrections_applied.sql
  - dbt_project/tests/assert_team_season_games_not_short_of_standings.sql
  - tests/test_no_decision_history_in_code.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - docs/tracker/**

impact_map: >
  writers: fixture_result_corrections → base_apif__fixtures_next (status AWD and the official score
  for a declared fixture); standings_corrections → base_apif__standings (the only writer of base
  standings).
  downstream of base_apif__standings (`dbt ls --select base_apif__standings+ --resource-type model`,
  pasted): base_apif__standings fct_standings int_team_season__deserved_vs_actual
  int_team_season__standings_primary mart_competition_fixtures mart_fixture_standing_context
  mart_match_days mart_matchday_insights mart_next_matchday mart_standings mart_team_profile
  mart_team_season mart_team_season_insights.
  downstream of base_apif__fixtures_next: every fixture-grained model (fct_fixture, int_legs__*,
  the team-season metrics, the marts), as for any existing fixture_result_corrections row.
  layer_rules: corrections are seeds applied in base (layering §2_base); no materialisation change.
  deploy_order: on merge the 04:00 nightly seeds and rebuilds; the MR build writes only ci_mr
  datasets.
  blast_radius: one fixture (884568, TSL 2022) becomes AWD 0–3, so Gaziantep FK and Trabzonspor
  count 36 games each; two AFCCL 2021 standings rows move from team 2937 to 2875. No other row
  changes.

decisions_taken: >
  The plan in #202, approved by the CPO in chat, 2026-10-05: standings_corrections gains an
  optional official_team_id. Readings, under the delegation of 2026-10-02:
  - A red league-table row is a result to research and declare: the Süper Lig match is declared
    from the TFF board decision without a question.
  - The Al Wahda rows keep the provider's figures (they are right); the correction is the team.
  - The test's paragraph explaining why it was a warning goes with the warning.

  Threshold declarations. NEW MECHANISM: none beyond the approved seed column. RECURRING COST: none.

decisions_reserved:
  - None.

done_when:
  - The MR data build passes with both tests at error and 0 rows from the standings games test.
  - pytest (whole suite), ruff, SQLFluff and the offline gates pass.
  - The review cycle passes, review.md bound to --staged-hash; the MR pipeline is green.
