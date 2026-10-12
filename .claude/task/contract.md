# Task contract — a played match's line-ups, shown only when right

objective: >
  Every played match gets one line-up state: confirmed (the provider's line-ups pass every check),
  researched (the line-ups come from an official source in the new seed fixture_lineup_corrections),
  or not_available. base_apif__lineups reads each team's latest line-up from stg_apif__lineups,
  pairs the substitutions and runs the checks; fct_fixture_lineup serves it on surrogate keys.
  For confirmed and researched matches only, mart_player_fixture_stats gains a row for every
  player on the team sheets, starter and substitute as the sheets say, the minute on and off and
  whom a substitute replaced, and mart_competition_fixtures serves each team's formation.
  mart_competition_fixtures serves lineup_state for every played match. A warn-only test lists the
  matches the research priority covers that are neither confirmed nor researched.

refs: >
  #176 (https://gitlab.com/rami.al-fahham/football-data-pipeline/-/work_items/176): the line-ups,
  step 2, and its research priority. The plan: approved in chat, 2026-10-12.

scope_paths:
  - dbt_project/models/1_staging/api_football/stg_apif__lineups.sql
  - dbt_project/models/2_base/api_football/base_apif__lineups.sql
  - dbt_project/models/2_base/api_football/base_apif__players.sql
  - dbt_project/models/2_base/api_football/base.yml
  - dbt_project/models/3_core/fct_fixture_lineup.sql
  - dbt_project/models/3_core/core.yml
  - dbt_project/models/5_marts/shared/mart_player_fixture_stats.sql
  - dbt_project/models/5_marts/shared/mart_competition_fixtures.sql
  - dbt_project/models/5_marts/shared/mart_team_momentum_window.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/models/docs/shared_columns.md
  - dbt_project/models/docs/cleaning_rules.md
  - dbt_project/seeds/fixture_lineup_corrections.csv
  - dbt_project/seeds/schema.yml
  - dbt_project/docs/layering.md
  - dbt_project/tests/assert_fixture_lineup_*.sql
  - dbt_project/tests/assert_mart_player_fixture_stats_*.sql
  - dbt_project/tests/assert_lineup_*.sql
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md

impact_map: >
  writers: the nightly ingest appends each finished match's fixture details, line-ups included, to
  RAW_APIF_FIXTURE_DETAILS, and stg_apif__lineups parses them; the new seed
  fixture_lineup_corrections holds researched line-ups, written by hand. Nothing else writes a
  line-up.
  downstream: on main, `dbt ls --select stg_apif__lineups+ fct_fixture_player_stats+
  mart_competition_fixtures+ base_apif__players+ --resource-type model` gives 44 models:
  base_apif__players dim_player fct_fixture_player_stats int_legs__player_match
  int_legs__team_from_players int_player_club_season__metrics
  int_player_competition_benchmark_metrics_long int_player_competition_benchmarks
  int_player_momentum__metrics int_player_profile__contribution int_player_profile__yoy
  int_player_season__metrics int_player_season__team int_player_season_position__metrics
  int_player_season_record int_team_competition_benchmark_metrics_long
  int_team_competition_benchmarks int_team_momentum__metrics int_team_profile__yoy
  int_team_season__deserved_vs_actual int_team_season__metrics
  int_team_season__metrics_cumulative int_team_season_record mart_competition_fixtures
  mart_leaderboards mart_match_days mart_matchday_insights mart_player_career
  mart_player_competition_benchmarks mart_player_fixture_stats mart_player_match_log
  mart_player_momentum mart_player_profile mart_player_season_record mart_roster
  mart_team_competition_benchmarks mart_team_leaderboards mart_team_momentum
  mart_team_momentum_window mart_team_profile mart_team_season mart_team_season_insights
  mart_team_season_record stg_apif__lineups. The branch adds base_apif__lineups,
  fct_fixture_lineup and the seed fixture_lineup_corrections.
  layer_rules: the seed is configuration applied in base; base resolves the latest fetch, unnests
  the sheets, pairs the substitutions and runs the checks against the squad lists, the transfers
  and the player stats, all base models; core projects onto surrogate keys and reads no JSON; the
  marts select and join.
  deploy_order: one dbt run; dbt seed precedes the models in data:build:main and fdp-nightly.
  blast_radius: dim_player gains every line-up player no other source names; every reader of
  dim_player joins it from a fact, so no reader gains rows. mart_player_fixture_stats gains a row
  for every team-sheet player without a stat line, and its is_starter and is_substitute follow the
  sheets, in confirmed and researched matches only; other matches keep today's rows and values.
  mart_team_momentum_window keeps has_player_stats by reading only stat-line rows.
  mart_competition_fixtures gains lineup_state and the two formations, which the export does not
  select. The export's matchstats files gain the new rows and columns; no site page reads them.
  The season starts and substitute appearances metrics read fct_fixture_player_stats and do not
  change.

decisions_taken: >
  A line-up is served only when confirmed by the checks or researched from an official source,
  otherwise not_available; the checks (two sheets, eleven starters each with a player id, the
  squad lists placing most of each sheet's players at its team and none only at the other team,
  the transfers in place of a missing squad list, no player on both sheets, no player the stats
  put on the other team, every substitution bringing on a substitute for a sheet player); no
  automatic relabelling of swapped sheets; the seed fixture_lineup_corrections on the
  fixture_goal_corrections pattern, its sources an official record or two match reports on
  different sites; lineup_state with values confirmed, researched and not_available beside
  goal_data_state; a warn-only research-list test following the #176 research priority; every
  sheet player gets a row, the sheets decide starter and substitute, the formation columns
  home_team_formation and away_team_formation; the substitution cleaning rule (a substitution
  event's player goes off and its assist comes on, except where the sheets name the assist a
  starter and the player not; measured in prod, the player is the starter in 449,852 of 457,143
  substitution events); shirt number and position from the stat line, then the sheet: approved in
  chat, 2026-10-12. A researched line-up is not held to the squad-list and transfer checks,
  because its official source outranks the provider's squad lists, and is held to every other
  check: approved in chat, 2026-10-12. The squad-list check passes a sheet with more of its
  players on its team's squad list than on the other team's and none listed only at the other
  team, not one needing over half its players listed (that would drop 657 confirmed matches,
  mostly for incomplete squad lists): approved in chat, 2026-10-12. Every lineup_state in base,
  core and the marts takes one of the three approved values; a provider sheet failing a check is
  not_available in every layer. Readings of the research priority: a club counts as one of those
  leagues' clubs in the seasons it plays in one of them; a walkover not played is left off the
  list, having no line-ups; the list carries each match's season so it is read current season
  first.

  THRESHOLD DECLARATIONS: NEW MECHANISM: none; a base model, a core fact, a correction seed and
  columns on existing marts, each on an existing pattern. RECURRING COST: about 1.2 to 1.5 GB more
  a night (building base_apif__lineups 0.31 GB, fct_fixture_lineup 0.20 GB, the marts' reads of
  it about 0.2 GB, base_apif__players about 0.06 GB, the new tests about 0.5 GB), measured by
  dry-run on prod; accepted in chat, 2026-10-12.

decisions_reserved:
  - The research rows of fixture_lineup_corrections (each batch its own MR).
  - Whether the season starts and substitute appearances metrics switch to the team sheets (a new issue).
  - The page and the played-match export (#175).
  - The merge of the two player-match marts (#176 step 3).

done_when:
  - dbt parse passes; sqlfluff shows no new finding on every changed model and test.
  - The changed models' compiled SQL against prod gives every played match one line-up state, keeps every stat-line row of mart_player_fixture_stats with no stat-line value changed except is_starter and is_substitute, and the new error tests return no rows.
  - mart_team_momentum_window's has_player_stats is unchanged against prod.
  - pytest tests/ passes; the offline CI gates pass; data:build:mr is green on the MR.

amendments: >
  Round 1 of review found decisions recorded without a named approval and checks weaker than their
  text. The researched-line-up exemption, the squad-list rule and the nightly cost were put to the
  CPO and approved in chat, 2026-10-12; the substitution rule and the shirt-number precedence are
  now named under the approvals they already had; the base and core state for a failing sheet is
  the approved not_available instead of a fourth value.
