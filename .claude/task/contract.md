# Task contract — every club the site shows has its country

objective: >
  78 teams in `dim_team` have no country because the provider sends none, SV Werder Bremen among
  them. A seed gives each one its country from an official source, applied in base like the team
  name overrides. A warn test reports any team with a Team page that still has no country, and a
  second reports a correction the provider has made unnecessary. The shared `team_country`
  description states when the column is NULL now.

refs: >
  #222, the Teams menu page (build plan approved in chat, 2026-10-30); design #133.

scope_paths:
  - dbt_project/seeds/team_country_corrections.csv
  - dbt_project/seeds/schema.yml
  - dbt_project/models/2_base/api_football/base_apif__teams_global.sql
  - dbt_project/tests/assert_team_country_corrections_still_needed.sql
  - dbt_project/tests/assert_shown_teams_have_a_country.sql
  - dbt_project/models/docs/shared_columns.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md

impact_map: >
  `team_country` is set in `base_apif__teams_global` and published by `dim_team`.
  `.venv/Scripts/dbt.exe ls --project-dir dbt_project --select base_apif__teams_global+
  --resource-type model` lists 29 models: base_apif__teams_global dim_player_team_season_mapping
  dim_team mart_competition_fixtures mart_fixture_standing_context mart_leaderboards
  mart_match_days mart_matchday_insights mart_player_career mart_player_fixture_stats
  mart_player_profile mart_roster mart_standings mart_team_competition_benchmarks
  mart_team_competitions mart_team_fixtures mart_team_leaderboards mart_team_market_value
  mart_team_momentum_window mart_team_profile mart_team_season mart_team_season_insights and the
  rest of the lineage. Readers of `team_country` (grep): dim_country, dim_team,
  mart_team_season_insights, mart_player_career, mart_player_profile, mart_team_market_value,
  mart_team_profile. blast_radius: only the 78 corrected teams change, from no country to their
  country; every country they get already exists in `countries.csv`, so `dim_country` gains no
  row. The team slug anchors on the provider's raw country (`team_country_raw`), so no URL moves.

decisions_taken: >
  The build plan approved in chat, 2026-10-30. The seed mirrors `team_name_overrides.csv`: keyed by
  `team_api_id` (equal to `team_sk`), with `source` and `note`, applied by a left join in
  `base_apif__teams_global`. Every source is the federation, league or competition organiser.
  Both tests warn with stored failures (approved in chat, 2026-10-30): a team without a country
  shows under the design's "no recorded country" group, so it is incomplete, not wrong.

decisions_reserved:
  - "none: no copy, label, order or page changes"

done_when:
  - The seed has one row per country-less team, each with an official source.
  - dbt parse passes; the seed's tests, the two warn tests and the base model compile.
  - The whole pytest and the offline gates of validate-local pass.
  - The MR's data:build:mr passes, and prod shows no shown team without a country.

amendments:
  - "Review round 1: `shared_columns.md` added to scope, so the `team_country` description names the corrections seed as the second source. Its exact sentence was approved in chat, 2026-10-31."
  - "Prod check: the provider now sends Red Star FC 93's country, so its row goes; Lourdes FC, new in the nightly, gets a row from the FFF. Both rows and a fourth review round approved in chat, 2026-10-31."
