# Task contract — One player under two provider ids in a match: sheet and stats line join on shirt

objective: >
  Issue #310. In one match, a team-sheet player whose provider id has no stats line of its own is
  the player of the same team whose stats line carries the same shirt number, when that stats-line
  player is named nowhere on the sheet. base_apif__lineups reads him under the stats-line id for
  that match only; hand overrides in player_id_overrides.csv keep precedence.
refs: "#310 (CPO, approved in chat 2026-11-14); #291 (where the gap was measured)"

scope_paths:
  - .claude/task/310-shirt-identity/**
  - dbt_project/models/2_base/api_football/base_apif__lineups.sql
  - dbt_project/models/2_base/api_football/base.yml
  - dbt_project/tests/assert_sheet_and_stats_player_join_on_shirt.sql

impact_map: >
  writers: base_apif__lineups (player_id of the paired sheet rows, and the ids of their substitution
  events within the model).
  downstream: `dbt ls --select base_apif__lineups+ --resource-type model` → 61 models, marts:
  mart_competition_fixtures mart_leaderboards mart_match_days mart_matchday_insights
  mart_player_career mart_player_competition_benchmarks mart_player_fixture_stats mart_player_index
  mart_player_momentum mart_player_profile mart_player_season_record mart_player_squad_benchmarks
  mart_player_window_metrics mart_roster mart_team_competition_benchmarks mart_team_competitions
  mart_team_index mart_team_leaderboards mart_team_momentum_window mart_team_page_window_metrics
  mart_team_profile mart_team_season mart_team_season_insights mart_team_season_record
  mart_team_window_metrics.
  layer_rules: entity alignment across two sources is base work (layering.md, 2_base); the model
  already reads base_apif__fixture_players and applies fixture_player_id there.
  deploy_order: no column, table or grain changes; ids change on the paired rows only.
  blast_radius: measured on prod 2026-11-14 (read-only, 185 MB) with every guard: 14,607 sheet rows
  are paired, on 8,587 team sheets in 7,173 matches, 43 competitions. Those players now join
  their stats lines: line-ups, match pages and player match rows show the stats-line player; the
  line-up checks squad_lists and player_stats_team read the joined ids.

decisions_taken: >
  CPO, approved in chat 2026-11-14 (#310): the rule is warehouse-wide, per match only, and hand
  overrides keep precedence. Engineering: a pair needs exactly one candidate per team, match and
  shirt, and per sheet id and per stats id in the match; a sheet id with a stats line anywhere in
  the match, or a stats player on any sheet row of the match, is not paired; a sheet id a hand
  override changed, or a card or goal correction names in that match, is not paired (hand data
  first); researched sheets are not paired (their ids are entered by hand). The substitution events of the match take the same pair, so a paired
  player's minutes on and off still join.
  Thresholds: no new mechanism, no recurring cost (CTEs on an existing model).

decisions_reserved:
  - none: the rule, its scope and its precedence are the CPO's approved wording on #310.

done_when:
  - dbt parse passes; sqlfluff lint clean; layer contract and description hygiene pass
  - full pytest passes
  - the singular test passes in data:build:mr, with the build green

amendments:
  - 2026-11-14: + the match-wide checks in decisions_taken — authority: engineering guards inside the CPO's #310 rule; content: data:build:mr found one sheet id whose stats line was filed under the other team.
  - 2026-11-14: + a sheet id that a card or goal correction names in a match is never paired there — authority: CPO, approved in chat 2026-11-14 (hand data stays as entered); content: data:build:mr found 14 card corrections naming a sheet id the pairing moved; this holds back 20 pairs.
