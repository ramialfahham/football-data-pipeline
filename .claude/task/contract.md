# Task contract — false player birth dates, details that change between builds, and their tests

objective: >
  Issue #260. A birth date that cannot be true is cleared in base. base_apif__players gets a fixed
  tie order, so two builds of the same data agree. A player whose records conflict shows a value
  checked against an outside source, or no value. Two dbt tests fail the build when either defect
  comes back.

refs: >
  #260, plan approved in chat 2026-11-06.

scope_paths:
  - dbt_project/macros/possible_birth_date.sql
  - dbt_project/macros/bio_correction.sql
  - dbt_project/models/2_base/api_football/base_apif__players.sql
  - dbt_project/models/2_base/api_football/base_apif__player_profiles.sql
  - dbt_project/models/2_base/api_football/base.yml
  - dbt_project/macros/player_id_override.sql
  - dbt_project/models/2_base/api_football/base_apif__fixture_players.sql
  - dbt_project/models/2_base/api_football/base_apif__fixture_events.sql
  - dbt_project/models/2_base/api_football/base_apif__lineups.sql
  - dbt_project/models/2_base/api_football/base_apif__player_team_season.sql
  - dbt_project/models/2_base/api_football/base_apif__squads.sql
  - dbt_project/models/2_base/api_football/base_apif__transfers.sql
  - dbt_project/seeds/player_id_overrides.csv
  - dbt_project/seeds/fixture_card_corrections.csv
  - dbt_project/seeds/fixture_lineup_corrections.csv
  - dbt_project/tests/assert_player_id_overrides_merged.sql
  - dbt_project/tests/assert_base_player_stats_cleaned.sql
  - dbt_project/models/docs/shared_columns.md
  - dbt_project/seeds/player_bio_corrections.csv
  - dbt_project/seeds/schema.yml
  - dbt_project/tests/assert_player_birth_date_possible.sql
  - dbt_project/tests/assert_player_bio_conflicts_settled.sql
  - site_v2/src/data/teams/211.json
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md

impact_map: >
  writers: dbt only. No ingestion code changes. The 249 missing profiles were fetched once through
  load_player_profiles_global, so RAW_APIF_PLAYER_PROFILES holds them before this MR.
  lineage: `dbt ls --resource-type model --select base_apif__players+ base_apif__player_profiles+`
  returns 2_base.api_football.base_apif__player_profiles, base_apif__players, 3_core.dim_player,
  5_marts.shared.mart_competition_fixtures, mart_leaderboards, mart_match_days, mart_player_career,
  mart_player_competition_benchmarks, mart_player_fixture_stats, mart_player_profile, mart_roster,
  mart_team_competitions, mart_team_index, mart_team_momentum_window.
  consumption: mart_player_profile derives age from player_birth_date and mart_roster carries it;
  the squad row leaves the age out when the date is empty, per wireframe 11.
  ci_layer_rules: scripts/check_layer_contract.py, scripts/check_description_hygiene.py.
  deploy_order: one merge; the nightly dbt build applies it. A deploy after that carries the values.
  blast_radius: 573 players lose a false birth date. About 249 tied players get one stable row. The
  corrections seed changes the players it lists. base_apif__players gains two boolean columns that
  no reader selects by position.

approved_design:
  - team: #134

acceptance_criteria:
  - No player shows a birth date that cannot be true; the three squad members dated 2026-07-06 in the sample show no date and no age on the built team page.
  - A player's name, birth date and nationality do not change between two builds of the same data.
  - A player whose records conflict shows a value checked against an outside source, or no value when none can be found.
  - A test fails the build on an impossible birth date.
  - A test fails the build on a conflict nobody has settled.

decisions_taken: >
  From the plan on #260, approved in chat 2026-11-06. New mechanism, declared: the seed
  player_bio_corrections. It holds one row per player and field, because an empty value there means
  "no value found" and a wide row could not tell that from "this field is not corrected". New
  mechanism, declared: two singular tests that fail the build. A failure on either skips what is
  built on the tested models in the nightly; the plan states this. Recurring cost: none measurable.
  The conflict flags are computed from rows base_apif__players already reads. The plan named
  dim_player as the place corrections apply; they apply in the two base models, because every
  correction seed in the project applies in base and dim_player publishes base unchanged, and the
  result is the same: a correction wins over every source.

decisions_reserved:
  - One name form for every player (initial or full), which stays mixed.
  - Country spellings in player nationality, which country_name_overrides does not reach today.

done_when:
  - python -m pytest tests passes.
  - dbt parse and sqlfluff pass on the changed models.
  - data:build:mr is green, both new tests included, each shown to fail on a fixed bad example.
  - The old-against-new comparison shows every changed row is a cleared date, a repaired tie or a correction.

amendments: >
  Both approved in chat, 2026-11-06, and recorded on #260. A profile value no longer settles a
  conflict: every conflict needs a checked correction. A new seed, player_id_overrides, merges one
  player's two provider ids, in the form of fixture_team_id_overrides with alias: first rows the 8
  pairs sorted as the same person. New mechanism, declared. It applies wherever a player id enters
  base: fixture_players, fixture_events, lineups, players, player_profiles, player_team_season,
  squads and transfers. No fetch holds both ids of a pair for one match, so no row is dropped.
  The id kept is the one with a birth date, otherwise the lower. The seed description's text was
  approved in chat, 2026-11-06. A test proves a merged player has one page and summed stats. The
  researched rows of fixture_card_corrections and fixture_lineup_corrections name the id kept.
