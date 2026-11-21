# Task contract — a zero offsides count the provider leaves empty in a full statistics line is a zero

objective: >
  Issue #335: in the cleaned team-match line, a blank offsides count is a zero when the team's own
  statistics line has values for fouls and possession, as a blank count is already a zero where
  the other team's line has a value for it. The provider leaves a zero count empty inside an
  otherwise full line, so a zero today cleans to a blank and withholds the offsides board for the
  whole competition (offsides per match is kept in 2 of 48 leagues).

refs: "#335; cleaning_rules (Blank rule); #334 (withhold rule that exposes the blanks)"

scope_paths:
  - .claude/task/335-blank-count-in-full-line/**
  - dbt_project/models/2_base/api_football/base_apif__fixture_statistics.sql
  - dbt_project/models/docs/cleaning_rules.md
  - dbt_project/tests/assert_team_stat_blank_counts_follow_the_blank_rule.sql
  - dbt_project/seeds/player_season_answer_key.csv
  - dbt_project/seeds/team_match_cleaning_answer_key.csv

impact_map: >
  writers: base_apif__fixture_statistics is the only model changed (the `filled` CTE, offsides).
  downstream: `.venv/Scripts/dbt.exe ls --select base_apif__fixture_statistics+ --resource-type
  model` lists 86 models. base (8): base_apif__fixture_events_checked, __fixture_players,
  __fixture_players_checked, __fixture_players_from_lineups, __fixture_statistics (the changed
  model), __lineup_sheets, __lineups, __players. core (5): dim_player, fct_fixture_event,
  fct_fixture_lineup, fct_fixture_player_stats, fct_fixture_team_stats. intermediate (40): the
  int_legs__*, int_player_*, int_team_* models and int_competition_season__player_stat_corrections,
  int_pipeline__corrections_no_longer_needed, int_standings__official_rank, among them
  int_team_season__metrics, int_team_window__metrics and int_team_momentum_window. marts (33):
  mart_competition_*, mart_player_*, mart_team_*, mart_head_to_head, mart_leaderboards, mart_match_days,
  mart_matchday_insights, mart_next_matchday, mart_roster, mart_standings and
  mart_fixture_standing_context, among them mart_team_leaderboards and mart_team_window_metrics.
  Every metric read from a team-match offsides count can change where a blank becomes 0: offsides
  per match, its windows and boards.
  player path: base_apif__fixture_players.sql lines 748 to 757 read the team's cleaned offsides as
  team_offsides and line 895 sets a player's blank offsides to 0 where the team's is 0, so a
  player's offsides in a match where the team line now cleans to 0 also becomes 0, and a player's
  season offsides, blank today because one match was blank and counted by nobody, gets a value.
  The hand-worked seed player_season_answer_key.csv states three such seasons as blank (Mbappé WC
  2026 fixtures 1569870 and 1578539, Olmo EURO 2024 fixtures 1145521 and 1225853, Kane BL1 2024
  fixtures 1224001, 1224011 and 1224130); the team lines of all seven fixtures carry fouls and
  possession and a blank offsides count (measured read-only on prod), so their rows and the three
  per-90 rows change in this MR: Mbappé 7 offsides in 698 minutes, Olmo 0 in 431, Kane 16 in 2,389
  (the sums of the other matches' provider values, read from fct_fixture_player_stats).
  layer_rules: base keeps cleaning only; no model, column or grain is added; the one singular test
  is in dbt_project/tests.
  deploy_order: the next nightly build rebuilds base and everything downstream in order; no
  consumer reads a new column.
  blast_radius: team-match lines of full statistics lines with a blank offsides count (measured
  21 Nov 2026 on prod core, all seasons: 4,644 of 101,724 full lines, the latest season 537 of
  1,062 blank offsides); free kicks and passes, blank in full lines because the provider does not
  send them, and card counts, which the match events already settle, are not touched. The compiled
  model run read-only on prod gives 0 blank offsides in full lines and 30 of 48 leagues with an
  offsides value for every team (2 before). The effect on boards is measured on the MR's ci_mr
  tables.

approved_design:
  - none: no page output changes by design; a team value that was blank can show where a value is served

depends_on:
  - none: base model on main alone
shared_files:
  - none: no design, registry, font or chart baseline changes

guard: >
  Measured read-only on prod core (all seasons): of the 4,644 team-matches that would become 0,
  202 have player lines with values and in 201 of them every player's offsides is 0; one
  (fixture 1180382, team 119, BSA 2024) has a player with an offside above 0, so the clause must
  not zero it. The coordinating session ruled that a blank team offsides count becomes 0 only when
  no player stat line of that team in the match, in any fetch, shows an offside above 0
  (stg_apif__fixture_players, read in the base model as a per-team maximum; the players' offsides
  are never summed into the team count, so no new derivation). The read adds one scan of the raw
  players JSON per build (about 0.8 GB, a few cents a night, no new run). Two hand-worked rows are
  added to team_match_cleaning_answer_key.csv: fixture 1180382 team 119 stays blank, fixture
  1145521 team 9 becomes 0.

decisions_taken: >
  A cleaning-rule extension (working_agreement §10, rule extensions): the coordinating session
  asked for it after measuring that half of the withheld offsides boards are our cleaning, and the
  CPO approves it by merging; the rule sentence is stated at the top of the MR head. The extension
  names offsides only, because the full-line evidence covers it (both teams blank in 5.3% of
  matches against about 4% expected for two independent zeros); card counts were checked and are
  left as they are, since the match events already settle them and a blank card count that stays
  blank has an event that could be that card. No new model, column, dependency, run or recurring
  cost.

decisions_reserved:
  - none: the clause and its scope are the approved issue text.

done_when:
  - dbt parse and sqlfluff lint of the base model and the test pass, and scripts/check_description_hygiene.py passes.
  - On the MR's ci_mr tables the new singular test returns 0 rows and the existing tests of base_apif__fixture_statistics, fct_fixture_team_stats and the player stats (assert_player_season_answer_key, assert_player_match_cleaning_answer_key, assert_base_player_stats_cleaned) pass.
  - On the ci_mr tables, offsides per match has a value for every team in about 30 of 48 leagues against 2, with the figures put in the MR.
  - python scripts/ci_local.py --mr is green on this branch.

amendments: (none)
