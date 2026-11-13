# Task contract — line-up rows: two people under one id, position codes, a player's team

objective: >
  Issues #281 and #213, and the off-format line-up position codes, batch E1 of the #290 data
  defects. A provider team sheet that names two people under one player id fails a line-up check,
  so the match shows no line-up until it is researched; a player listed twice under one name keeps
  his first listing on every build. Every position code is G, D, M or F, or empty. A researched
  line-up decides a player's team in that match on every page, and Austin FC–LAFC of 2 November
  2025 is researched from the league's official match data.

refs: >
  #281, #213, #290. Batch E1, the sheet rule for two people under one id, the grid-row rule for
  wingers and the name mapping approved in chat, 2026-11-12, through the coordinating session.
  The off-format position codes were found by the Statistics data stream (#291 area).

scope_paths:
  - .claude/task/290-e1-lineups/
  - dbt_project/models/2_base/api_football/base_apif__lineups.sql
  - dbt_project/models/2_base/api_football/base_apif__fixture_players.sql
  - dbt_project/models/2_base/api_football/base_apif__fixture_events.sql
  - dbt_project/models/2_base/api_football/base.yml
  - dbt_project/models/docs/cleaning_rules.md
  - dbt_project/models/docs/shared_columns.md
  - dbt_project/models/3_core/core.yml
  - dbt_project/seeds/fixture_lineup_corrections.csv
  - dbt_project/seeds/player_match_cleaning_answer_key.csv
  - dbt_project/tests/assert_lineup_two_people_one_id_not_held.sql

impact_map: >
  writers: base_apif__lineups is the only writer of a match's line-up rows and lineup_state; it
  reads stg_apif__lineups, fixture_lineup_corrections and base_apif__fixture_players (the
  player_stats_team check). base_apif__fixture_players is the only writer of a provider stat line;
  it reads stg_apif__fixture_players and, after this change, fixture_lineup_corrections for the
  team of a player in a researched match (no cycle: it never reads base_apif__lineups).
  base_apif__fixture_events writes each event's team and resolved_player_team_id, which
  base_apif__fixture_players reads; it takes a researched player's team from the same seed, so a
  researched player's events and stat line name the same team. The cleaning_rules doc block and
  the position_code__leg doc in shared_columns.md state the rules these models apply.
  downstream: `dbt ls --select base_apif__lineups+ base_apif__fixture_players+
  fixture_lineup_corrections+ --resource-type model` (run 2026-11-12) gives 62 models, 25 marts:
  mart_competition_fixtures mart_leaderboards mart_match_days mart_matchday_insights
  mart_player_career mart_player_competition_benchmarks mart_player_fixture_stats mart_player_index
  mart_player_momentum mart_player_profile mart_player_season_record mart_player_squad_benchmarks
  mart_player_window_metrics mart_roster mart_team_competition_benchmarks mart_team_competitions
  mart_team_index mart_team_leaderboards mart_team_momentum_window mart_team_page_window_metrics
  mart_team_profile mart_team_season mart_team_season_insights mart_team_season_record
  mart_team_window_metrics. Line-up rows reach the player-match fill
  (base_apif__fixture_players_from_lineups, confirmed and researched only), fct_fixture_lineup and
  fct_fixture_player_stats, and from there every player and team metric built on a player match.
  layer_rules: base only (dedup, entity alignment, a line-up check); no per-competition logic, no
  partition_by or cluster_by; the position mapping names provider codes, not competitions.
  deploy_order: column values and one more check value in base; no column added or removed. The
  merge rebuilds everything downstream in data:build:main.
  blast_radius: measured on prod, 2026-11-12. Two people under one id: 105 (match, team, player)
  groups on the provider's latest sheets, 58 of them a starter and a substitute that today keep
  the starter silently; 86 matches, of which 25 confirmed today become not_available (5 from the
  2026 seasons; LIBER, UEL, AFCCL, CAFCL, UECL, LP), 60 are not_available already and 1 is
  researched (unchanged). The same person listed twice: 29 groups, now the first listing on every
  build. Position codes: 2,688 fct_fixture_lineup rows change (Veikkausliiga 2022, 107 matches,
  2,323 rows mapped to G/D/M/F; SUB 230 and '-' 135 to empty) and 138 provider stat lines (SUB 43,
  '-' 95) to empty; those reach fct_fixture_player_stats (2,597 rows) and the position groups
  built on it. A player's team: Austin FC–LAFC (fixture 1482409) becomes researched, both sheets
  on their own team, and Ilie Sánchez's stat line and his two events (a yellow card and his
  substitution) move from LAFC to Austin FC; LAFC's sheet takes the league's 4-3-3 and the
  league's positions (Palencia and Hollingshead D, Jailson M). No other researched match has a
  stat line or an event under the other team today (22 MB query, 0 events).

approved_design:
  - none: no page output changes; the marts the pages read change values only

decisions_taken: >
  Rulings in chat, 2026-11-12, through the coordinating session: a team sheet with two people
  under one id fails a line-up check, so the match shows no line-up until researched; position
  codes take the name mapping (goalkeeper G; left_back, right_back, central_de D; central_mi M;
  striker F) and, for the wingers (left_winge, right_wing), the code of the player's row on the
  sheet's grid against the formation (first row G, second D, last F, rows between M), which
  matches the provider's own codes in about 94% of Veikkausliiga 4-4-2 rows; #213 in this batch.
  "Two people" means two different names under one id on one team's sheet; one name listed twice
  is one person and keeps the first listing (starters before the bench, then sheet order), which
  makes the pick total. Every other code (SUB, '-', any new one) is empty: it names no position.
  A researched line-up sets a player's team in that match in base_apif__fixture_players, from the
  same seed, so the stat line and the sheet agree and the existing player_stats_team check holds
  for a researched match whose only conflict was a stat line under the other team (#213's second
  line). No new mechanism: the check is one more value of failed_checks; the answer key and the
  research seed are existing seeds.

  The exact text of the three cleaning_rules lines (a researched line-up decides a player's team;
  positions; the two-people-one-id check): approved in chat, 2026-11-12, through the coordinating
  session, and used word for word.

decisions_reserved:
  - none: the cleaning_rules text, the only open question, is answered above.

done_when:
  - dbt parse passes; SQLFluff passes on the changed models and the new test; the offline gates
    and the full pytest pass.
  - The changed base models, compiled and run read-only on prod, reject the sheets with two names
    under one id, give every position a G/D/M/F code or empty, and put Sánchez at Austin FC.
  - Tests that fail on prod today and pass after: assert_lineup_two_people_one_id_not_held (25
    confirmed matches today), accepted_values G/D/M/F on fct_fixture_lineup.position_code (2,688
    rows) and fct_fixture_player_stats.position_code (2,597 rows), and the new
    player_match_cleaning_answer_key row that puts Sánchez at Austin FC in fixture 1482409.
  - On the MR's ci_mr tables these, assert_lineup_researched_matches_hold and
    assert_player_match_cleaning_answer_key return no rows; compared with prod, only the listed
    matches, rows and positions change.

amendments: (none)
