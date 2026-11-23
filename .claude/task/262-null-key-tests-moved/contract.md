# Task contract - a provider key that is NULL in staging, and that base drops, is no longer tested in staging

objective: >
  Issue #262, box "Only a check that catches a defect in our own code stops the nightly." Seventeen
  error-severity not_null tests on the staging models fail the build when the provider's payload
  carries a NULL key (fixture_id, team_id, league_api_id, season_api_year, coach_id, player_id, a
  standings season). Base already drops the NULL-key rows and carries its own not_null test on the
  same key. Now the staging tests are removed and the base tests are the proof that the drop works.
  A match where base loses a value to its team-id filter is listed by match on
  mart_competition_research_list as null_key_line_withheld (base model
  base_apif__fixture_lines_without_key, one macro lines_without_key), at error like the other
  listing kinds. The rule is base's own selection: a statistics line with a fixture id and no team
  id that carries a value for a stat which a team of the match has from no line with a team id, in
  any fetch (the way base_apif__fixture_statistics merges the newest value of each stat from any
  fetch), and a line-up with a fixture id and no team id in a match where a team has no sheet in
  base_apif__lineup_sheets. A match whose teams all have their values from lines with a team id is
  not listed, whichever fetch the line with no team id is in. The rule is proven by an error test
  derived from staging and by a hand-written answer key. A line with no fixture id names no match
  and is dropped without a row, as are the NULL-key rows of the other moved models. The staging
  tests of the player stat lines (stg_apif__fixture_players: fixture_id, team_id, player_id) stay as
  they are: they are the next change. A base model that reads staging without the key filter
  (base_apif__teams) gets it, so a NULL key cannot reach a team, and a singular test that
  recomputes a rule of base from a moved staging model carries the filter base applies. A python
  test pins the move: no removed staging test is back, each has its base proof in yml at error
  without a filter, every base filter that drops a NULL key is in the SQL, every read of a moved
  staging model is pinned, and the listing model and the mart branch are pinned. The staging yml
  header, layering.md and engineering_standards.md state the policy.

refs: >
  #262 What exactly / How (approved in chat, 15 Nov 2026). The coordinating session ruled: where a
  provider key NULL is dropped in base, the staging test becomes a base test that proves the drop,
  and the dropped value is listed if the match can be identified. Standing own-key tests (our
  surrogate keys) stay at error. Not in this change: a staging NULL that base passes on
  (home_team_id, team_name, fixture_date, and player_teams.team_id, which no model reads), the
  uniqueness tests of staging, the player stat lines (stg_apif__fixture_players: their tests, base
  filters, listing and any recovery through a seed are their own change).

depends_on:
  - none: every file this change edits is on gitlab/main

shared_files:
  - none: no design baseline, chart manifest or chart pin is changed

scope_paths:
  - dbt_project/models/1_staging/api_football/stg_apif__generic.yml
  - dbt_project/models/2_base/api_football/base_apif__teams.sql
  - dbt_project/models/2_base/api_football/base_apif__fixture_lines_without_key.sql
  - dbt_project/models/2_base/api_football/base.yml
  - dbt_project/macros/lines_without_key.sql
  - dbt_project/models/5_marts/shared/mart_competition_research_list.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/docs/layering.md
  - dbt_project/docs/engineering_standards.md
  - dbt_project/tests/assert_null_key_lines_listed.sql
  - dbt_project/tests/assert_lines_without_key_answer_key.sql
  - dbt_project/tests/assert_team_id_aliases_merged.sql
  - dbt_project/tests/assert_league_name_overrides_are_corrections.sql
  - tests/test_staging_key_tests_moved.py
  - tests/test_null_key_lines_wiring.py
  - tests/test_lineup_ties_wiring.py
  - .claude/skills/research-provider-errors/SKILL.md
  - .claude/task/262-null-key-tests-moved/contract.md
  - .claude/task/262-null-key-tests-moved/review.md
  - .claude/task/262-null-key-tests-moved/review_input.patch

impact_map: >
  writers: the yml of twelve staging models loses 17 not_null tests, one base model gains key
  filters (base_apif__teams: fixture_id on the statistics and events reads and on fixtures_next,
  season on standings), one base model, one macro, one mart branch and two singular tests are
  added, and two singular tests gain the filters of base on reads of a moved staging model:
  assert_team_id_aliases_merged (its fixture and standings reads) and
  assert_league_name_overrides_are_corrections (its leagues read). Every other singular test that
  reads one of the twelve moved staging models was read in full: those that recompute a rule of
  base carry its key filter already, and the rest (assert_country_name_overrides_still_needed,
  test_stg_fixture_statistics_non_empty, assert_goal_added_minute_from_newest_fetch,
  assert_fixture_events_only_from_latest_fetch) compare strings, count rows or join on the key, so a
  NULL-key row changes none of their results. The tests removed (`dbt ls --select <model>
  --resource-type test`): not_null_stg_apif__fixtures_next_fixture_id,
  not_null_stg_apif__fixture_events_fixture_id, not_null_stg_apif__fixture_statistics_fixture_id,
  not_null_stg_apif__fixture_statistics_team_id, not_null_stg_apif__lineups_fixture_id,
  not_null_stg_apif__lineups_team_id, not_null_stg_apif__teams_team_id,
  not_null_stg_apif__leagues_league_api_id, not_null_stg_apif__leagues_season_api_year,
  not_null_stg_apif__players_player_id, not_null_stg_apif__players_team_id,
  not_null_stg_apif__player_profiles_player_id, not_null_stg_apif__squads_player_id,
  not_null_stg_apif__squads_team_id, not_null_stg_apif__standings_season,
  not_null_stg_apif__coaches_coach_id, not_null_stg_apif__coach_career_coach_id.
  Each key has a base proof already in yml (`not_null` on the column): base_apif__fixtures_next,
  base_apif__fixture_events, base_apif__fixture_statistics, base_apif__lineup_sheets,
  base_apif__teams, base_apif__leagues, base_apif__players, base_apif__squads,
  base_apif__standings, base_apif__coaches, base_apif__coach_career, base_apif__player_profiles,
  base_apif__player_team_season.
  The changed models and their readers, from `dbt ls --select <model>+ --resource-type model` (the
  .venv dbt, repo root, measured on this branch): base_apif__teams+ lists 89 models, 34 of them
  marts: base_apif__teams, base_apif__teams_global, base_apif__venues,
  dim_player_team_season_mapping, dim_team, dim_venue, fct_fixture, fct_fixture_team_stats and every
  model and mart downstream of dim_team and fct_fixture. base_apif__fixture_lines_without_key+
  lists 2 models: itself and mart_competition_research_list. tests/test_lineup_ties_wiring.py pins
  the research-list branch of lineup_duplicate_withheld and the accepted values of check_name, which
  this change extends, so its two pins move with the change. The new model reads stg_apif__fixture_statistics,
  stg_apif__lineups, base_apif__fixtures_next, base_apif__lineup_sheets and the seed
  fixture_team_id_overrides; none of those changes.
  downstream: the filters drop only a staging row whose fixture_id or standings season is NULL, and
  the new model reads staging and base only. The key tests of staging passed before this change, so
  prod holds no such row: no row, no number and no page changes, and the new row kind is empty today.
  layer_rules: tests, yml, base filters, one base model, one macro, one mart branch;
  check_layer_contract applies unchanged.
  deploy_order: one build; the nightly picks it up after merge.
  blast_radius: none for any model or value today. The not_null checks on a provider key in staging
  fall from 17 to 0, and no test is at warn. The staging tests of the player stat lines and the
  staging uniqueness tests stay at error. A uniqueness test of staging that groups on a key column
  (the order-keys tests of events, standings, teams and leagues) still fails on two NULL-key rows
  with the same other columns in one fetch, because dbt_utils.unique_combination_of_columns groups
  NULLs: that interaction is not closed by this change. Its owners are the coordinating session's
  splits of #262: split 2b for the events test, split 2d for the standings, teams and leagues
  tests. The column test unique on stg_apif__fixtures_next.fixture_id ignores NULLs, so it needs no
  owner. Split 1b (the player stat lines) does not cover it.
  recurring_cost: the new base model reads two staging tables and dry-runs at 106 MB per build, and
  assert_null_key_lines_listed at 260 MB at most per run. Together that is about 0.37 GB a night,
  about 11 GB a month, well under one dollar a month at on-demand rates.

approved_design:
  - none: no page output changes

decisions_taken: >
  Ruled by the coordinating session on #262's approved rule (approved in chat, 15 Nov 2026). The
  staging NULL test is a provider-data check; the base model drops the row and its own not_null
  proves the drop. A match where base loses a value to the team-id filter is listed by match as
  null_key_line_withheld with seed none: no seed row can name a line with no team id, a fetch that
  carries the id removes the row. The row kind is named after the existing *_withheld kinds
  (engineering decision, working agreement section 10 unclear cases). Rows with no identifiable
  match, which means a line with no fixture id and the NULL-key rows of the other moved models, are
  dropped without a row, as the ruling says: listed if the match can be identified. The six
  uniqueness tests of staging stay at error: the ruling names NULL keys, and a duplicate at the
  grain of a staging model can come from our own flatten. The player stat lines stay as they are
  until their own change. Base models that read staging without the key filter get it. The header
  comment of the staging yml, layering.md and engineering_standards.md state the policy: a provider
  key that base drops when NULL is tested in base, not in staging, except in
  stg_apif__fixture_players, which keeps its own tests. The recurring cost of the new
  model and test is measured in the impact map and is far below the amount that goes to the CPO.

decisions_reserved: >
  none: no page, metric, name or rule is added.

done_when:
  - python scripts/ci_local.py --mr passes
  - dbt parse passes
  - python -m pytest tests/test_staging_key_tests_moved.py tests/test_null_key_lines_wiring.py passes, and fails with a removed staging test restored, a base proof lowered, a base filter removed or the listing model or the mart branch changed
  - the MR pipeline is green, data:build:mr included

amendments: (none)
