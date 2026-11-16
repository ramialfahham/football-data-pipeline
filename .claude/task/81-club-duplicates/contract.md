# Task contract — one club, one team id

objective: >
  Issue #81. Where the provider holds two team ids for one club, the club shows as two teams with
  two pages. The fixture_team_id_overrides seed already has an `alias` mode for this ("the provider
  holds two ids for one club"), but only the per-match feeds and their dim_team keys apply it: the
  fixture list, standings, the /teams rows, squads, rosters, coaching stints and transfers keep the
  duplicate id, so the duplicate survives as a team of its own. This task applies `alias` wherever a
  base model takes a team id, the way player_id_override applies a merged player id (#260), and adds
  the duplicate pairs found in prod with their sources.

refs: >
  #81 (go-live gate #290). Known cases: Nyasa Big Bullets 4596/4599; Whitecaps 8007 and Vancouver
  Whitecaps 1603 (the #277 comparison on !450: linking them restores the line-up of CCCU 253504).

scope_paths:
  - .claude/task/81-club-duplicates/
  - dbt_project/macros/team_id_override.sql
  - dbt_project/models/2_base/api_football/base_apif__fixtures_next.sql
  - dbt_project/models/2_base/api_football/base_apif__standings.sql
  - dbt_project/models/2_base/api_football/base_apif__teams.sql
  - dbt_project/models/2_base/api_football/base_apif__squads.sql
  - dbt_project/models/2_base/api_football/base_apif__coach_career.sql
  - dbt_project/models/2_base/api_football/base_apif__player_team_season.sql
  - dbt_project/models/2_base/api_football/base_apif__transfers.sql
  - dbt_project/models/2_base/api_football/base.yml
  - dbt_project/seeds/fixture_team_id_overrides.csv
  - dbt_project/seeds/team_country_corrections.csv
  - dbt_project/seeds/schema.yml
  - dbt_project/tests/assert_team_id_aliases_merged.sql

impact_map: >
  writers: each changed base model has one writer, itself, built by dbt from staging
  (stg_apif__fixtures_next, _standings, _teams, _squads, _coach_career, _players, _transfers) and
  the fixture_team_id_overrides seed. No raw table, loader or export script changes.
  downstream: `dbt ls --resource-type model --output name --select base_apif__fixtures_next+
  base_apif__standings+ base_apif__teams+ base_apif__squads+ base_apif__coach_career+
  base_apif__player_team_season+ base_apif__transfers+` gives 105 models. Base (16):
  base_apif__coach_career base_apif__fixture_events base_apif__fixture_fetches
  base_apif__fixture_players base_apif__fixture_players_from_lineups base_apif__fixture_statistics
  base_apif__fixtures_next base_apif__lineup_sheets base_apif__lineups base_apif__player_team_season
  base_apif__players base_apif__squads base_apif__standings base_apif__teams base_apif__teams_global
  base_apif__transfers. Intermediate (44): int_competition_season__player_stat_corrections
  int_knockout_ties int_legs__player_match int_legs__team_from_players int_legs__team_match
  int_player__national_team_minutes int_player__page_profile int_player_club_season__metrics
  int_player_competition_benchmark_metrics_long int_player_competition_benchmarks
  int_player_match__metrics int_player_momentum__metrics int_player_page__window_seasons
  int_player_profile__contribution int_player_profile__yoy int_player_season__metrics
  int_player_season__team int_player_season_position__metrics int_player_season_record
  int_player_squad_window__metrics int_player_window__metrics int_round_names
  int_standings__official_rank int_standings__section_kinds
  int_team__current_national_competitions int_team__featured_season
  int_team_competition_benchmark_metrics_long int_team_competition_benchmarks
  int_team_competition_phase__metrics int_team_momentum__metrics int_team_momentum_window
  int_team_profile__streaks int_team_profile__yoy int_team_season__biggest_results
  int_team_season__deserved_vs_actual int_team_season__longest_runs int_team_season__metrics
  int_team_season__metrics_cumulative int_team_season__standings_primary
  int_team_season__table_by_time int_team_season__table_legs int_team_season__table_state
  int_team_season_record int_team_window__metrics. Core (12) and marts (33):
  dim_coach_team_mapping dim_player dim_player_team_season_mapping dim_team
  dim_team_competition_season_mapping fct_fixture fct_fixture_event fct_fixture_lineup
  fct_fixture_player_stats fct_fixture_team_stats fct_standings fct_transfer
  mart_competition_fixtures mart_competition_index mart_competition_season_summary
  mart_fixture_standing_context mart_head_to_head mart_leaderboards mart_match_days
  mart_matchday_insights mart_next_matchday mart_player_career mart_player_competition_benchmarks
  mart_player_fixture_stats mart_player_index mart_player_momentum mart_player_profile
  mart_player_season_record mart_player_squad_benchmarks mart_player_window_metrics mart_roster
  mart_standings mart_team_competition_benchmarks mart_team_competitions mart_team_fixtures
  mart_team_index mart_team_leaderboards mart_team_market_value mart_team_momentum_window
  mart_team_page_window_metrics mart_team_profile mart_team_season mart_team_season_insights
  mart_team_season_record mart_team_window_metrics.
  layer_rules: base = dedup and first logic, so the id correction sits in base, as the existing
  alias joins and player_id_override do; check_layer_contract.py, no per-competition file.
  deploy_order: models and seeds only; prod picks the change up at the first nightly after the
  merge. No migration, no raw change, nothing breaks before the merge.
  blast_radius: only rows of the 8 duplicate ids and the 5 Europa FC ties change. Each duplicate
  id leaves dim_team and every fact, its matches, standings rows, squad, roster, stints and
  transfers move to the id kept, and its page goes. The id kept gains those rows; Nyasa Big
  Bullets 4599's slug loses its `-malawi-4599` suffix under the existing slug rule, since its
  name is no longer contested. CCCU 253504 (2016) gets its line-up back. The 5 Europa FC ties
  move from CE Europa 593 to Europa FC 10125. Goals, points and results of every match stay as
  they are; a standings row changes only its team id. The comparison of the MR's ci_mr tables
  against prod lists every team, fixture and standings row that changed.

depends_on:
  - none: builds on gitlab/main 5db6166e; no open MR touches these files.

shared_files:
  - none: no design baseline, chart manifest or chart pin changes.

approved_design:
  - none: no page output changes; the diff touches no site_v2/src/ file or export script

decisions_taken: >
  Applying `alias` to standings, the /teams rows, squads, rosters, coaching stints and transfers,
  and the new text of the fixture_team_id_overrides seed description and its wrong_team_api_id
  column: approved in chat, 2026-11-16.
  No new mechanism: `alias` is the existing mode of fixture_team_id_overrides, whose description
  already says it replaces the id unconditionally; this task applies it in the base models that did
  not. team_id_override is a dbt macro of the same shape as player_id_override (#260), not a new
  object class. `reattribute_in_fixture` is the existing mode of the shared-id work (#238).
  A pair is linked only with proof that the two ids are one club: an external source naming the
  club in the duplicate id's matches, plus our own data (players shared, same venue, or one club
  across consecutive rounds of one cup). Never by name alone. The id kept is the one with the
  provider's fuller /teams record and the longer history. A duplicate id's own rows in
  team_country_corrections go with it, since the id kept holds its country.
  No recurring cost: no provider call, no extra run.

decisions_reserved:
  - Folding two clubs that merged (Bury 1344 and Bury AFC 17021) is not done here; a merger is not
    a provider duplicate.

done_when:
  - dbt parse passes; sqlfluff lint of every changed model passes from the repo root.
  - python -m pytest tests/ -q is green and the offline gates pass.
  - python scripts/ci_local.py --mr passes before every review round and push.
  - The MR pipeline is green and data:build:mr passes, assert_team_id_aliases_merged included.
  - A read-only comparison of the MR's ci_mr tables against prod, under 20 GB, lists every team,
    fixture and standings row that changed, and shows CCCU 253504's line-up.

amendments: (none)
