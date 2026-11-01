# Task contract — Red Star de Bangui gets its own team id

objective: >
  The provider files Red Star de Bangui (Central African Republic) under Red Star FC 93's team id
  104 in two CAF Champions League 2024 matches, fixtures 1239850 and 1239851. Red Star de Bangui
  has no provider id. It gets our own team id -1, named Red Star, country Central African
  Republic, and both matches move to it in the fixture list and every match feed. Red Star FC 93
  keeps all its own matches.

refs: >
  `#238`, Red Star FC 93 shows two CAF Champions League matches Red Star de Bangui played. Plan
  (path A) approved in chat via plan mode.

scope_paths:
  - dbt_project/seeds/fixture_team_id_overrides.csv
  - dbt_project/seeds/team_name_overrides.csv
  - dbt_project/seeds/team_country_corrections.csv
  - dbt_project/seeds/schema.yml
  - dbt_project/models/2_base/api_football/base_apif__fixtures_next.sql
  - dbt_project/models/2_base/api_football/base_apif__fixture_events.sql
  - dbt_project/models/2_base/api_football/base_apif__fixture_players.sql
  - dbt_project/models/2_base/api_football/base_apif__fixture_statistics.sql
  - dbt_project/models/2_base/api_football/base_apif__lineups.sql
  - dbt_project/models/2_base/api_football/base_apif__teams.sql
  - dbt_project/models/2_base/api_football/base.yml
  - dbt_project/tests/assert_base_team_stats_cleaned.sql
  - dbt_project/tests/assert_fixture_team_id_overrides_applied.sql
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md

impact_map: >
  writers: the six base models named in scope_paths are the only readers of
  fixture_team_id_overrides; base_apif__teams_global is the only reader of team_name_overrides and
  team_country_corrections.
  downstream: `.venv/Scripts/dbt.exe ls --project-dir dbt_project --select
  base_apif__fixtures_next+ base_apif__fixture_events+ base_apif__fixture_players+
  base_apif__fixture_statistics+ base_apif__lineups+ base_apif__teams+ fixture_team_id_overrides+
  team_name_overrides+ team_country_corrections+ --resource-type model` lists 79 models, 29 of them
  marts: mart_competition_fixtures, mart_competition_index, mart_competition_season_summary,
  mart_fixture_standing_context, mart_head_to_head, mart_leaderboards, mart_match_days,
  mart_matchday_insights, mart_next_matchday, mart_player_career,
  mart_player_competition_benchmarks, mart_player_fixture_stats, mart_player_momentum,
  mart_player_profile, mart_player_season_record, mart_roster, mart_standings,
  mart_team_competition_benchmarks, mart_team_competitions, mart_team_fixtures, mart_team_index,
  mart_team_leaderboards, mart_team_market_value, mart_team_momentum_window, mart_team_profile,
  mart_team_season, mart_team_season_insights, mart_team_season_record, mart_team_window_metrics.
  layer_rules: the corrections are seeds applied in base, as the existing override modes are;
  check_layer_contract.py applies unchanged.
  deploy_order: seeds and models change together in the one prod build after merge; nothing
  breaks before it, the two fixtures simply stay under 104 until then.
  blast_radius: only rows of fixtures 1239850 and 1239851 change. Team 104 loses its two CAF
  Champions League 2024 matches (played 2, W0 D1 L1 on today's prod); a new team -1 gains them,
  with its events, line-ups, team and player statistics. No other fixture's team id moves, since
  the new mode is keyed on the fixture id.

approved_design:
  - "none: no page output changes; the marts gain team -1 and lose 104's two CAF rows, and no page layout or field changes"

decisions_taken: >
  Approved in chat via plan mode: path A. Team id -1 is ours, not the provider's, named Red Star
  with country Central African Republic, both sourced to CAF's preliminary-round fixture list.
  fixture_team_id_overrides gains a fixture_id column and a third mode, reattribute_in_fixture,
  that replaces the wrong id with the correct one inside the named fixture only, and outranks the
  other two modes. It is applied in the fixture list, the four match feeds, the team keys and the
  team statistics test's own replay of the overrides. A new error test fails while a
  reattribute_in_fixture row is not applied.
  NEW MECHANISM declared: a team id the provider never sent (-1), and the per-fixture override
  mode. Both are part of the approved plan.

decisions_reserved:
  - "none: every decision of this task is approved, see decisions_taken"
  - "Out of scope, each its own decision later: Newmarket, Victoria United and Warriors FC, whose provider ids show the same shared-id shape."

done_when:
  - dbt parse, SQLFluff on the changed SQL, pytest and the offline gates pass.
  - The new test returns the two fixtures on today's prod data, read-only.
  - The changed models' compiled SQL, run read-only on prod with the seed rows inlined, puts both fixtures under -1 and none under 104, and the new test then returns no row.

amendments: (none)
