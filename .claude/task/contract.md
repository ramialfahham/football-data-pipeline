# Task contract — a player's row and his match events under one team: the squad list decides

objective: >
  The issue "A player's row and his match events in different teams: move the side the squad list
  contradicts" (#189). Where a player's statistics row and his match events place him in different
  teams of the match, the squad list (base_apif__player_team_season) decides, and his other
  matches decide where it names both teams or neither; the side it contradicts moves to the team
  it names: the events in base_apif__fixture_events or the row in base_apif__fixture_players. A
  test fails when a cleaned player row and that player's events in the match sit under different
  teams. fct_fixture_event re-merges each match whose stored events name a different team than
  base, so moved events reach its history without a full rebuild.

refs: >
  #189, rewritten and approved by the CPO on 2026-10-03; its How step 3 edited on 2026-10-04 with
  the CPO's answer in chat that day.

acceptance_criteria:
  # The issue's checklist lines, verbatim.
  - "Where a player's row and his match events place him in different teams of the match, the squad list decides, and his other matches decide where it names both teams or neither: the side it contradicts, the row in `base_apif__fixture_players` or the events in `base_apif__fixture_events`, moves to the team it names."
  - "A test fails when a cleaned player row and that player's events in the match sit under different teams."

scope_paths:
  - dbt_project/models/2_base/api_football/base_apif__fixture_events.sql
  - dbt_project/models/2_base/api_football/base_apif__fixture_players.sql
  - dbt_project/models/2_base/api_football/base.yml
  - dbt_project/models/3_core/fct_fixture_event.sql
  - dbt_project/models/3_core/core.yml
  - dbt_project/models/docs/cleaning_rules.md
  - dbt_project/tests/assert_player_row_and_events_same_team.sql
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md
  - .claude/task/audit_reviewer_outputs.md
  - docs/tracker/**

impact_map: >
  writers: base_apif__fixture_events and base_apif__fixture_players are each written only by their
  own model, rebuilt in full every night; fct_fixture_event is the incremental fact merged from
  base_apif__fixture_events on event_sk.
  downstream, `dbt ls --project-dir dbt_project --select base_apif__fixture_events+
  base_apif__fixture_players+ --resource-type model` (54 models, 24 marts):
  base_apif__fixture_events base_apif__fixture_players base_apif__fixture_statistics
  base_apif__players dim_player fct_fixture_event fct_fixture_player_stats fct_fixture_team_stats
  int_legs__player_match int_legs__team_from_players int_legs__team_match
  int_player_club_season__metrics int_player_competition_benchmarks int_player_momentum__metrics
  int_player_profile__contribution int_player_profile__yoy int_player_season__metrics
  int_player_season__team int_player_season_position__metrics int_player_season_record
  int_team_competition_benchmark_metrics_long int_team_competition_benchmarks
  int_team_momentum__metrics int_team_momentum_window int_team_profile__streaks
  int_team_profile__yoy int_team_season__deserved_vs_actual int_team_season__metrics
  int_team_season__metrics_cumulative int_team_season_record mart_competition_fixtures
  mart_competition_season_summary mart_head_to_head mart_leaderboards mart_match_days
  mart_matchday_insights mart_player_career mart_player_competition_benchmarks
  mart_player_fixture_stats mart_player_match_log mart_player_momentum mart_player_profile
  mart_player_season_record mart_roster mart_team_competition_benchmarks mart_team_fixture_stats
  mart_team_fixtures mart_team_leaderboards mart_team_momentum mart_team_momentum_window
  mart_team_profile mart_team_season mart_team_season_insights mart_team_season_record.
  fct_fixture_event has no model reader (`dbt ls --select fct_fixture_event+1` lists only itself);
  four tests read it.
  layer_rules: base reads stg_apif__fixture_players and base_apif__player_team_season (base may
  read staging and base); no core, intermediate or mart ref; no model sets its materialisation;
  fct_fixture_event stays the one incremental core fact; check_layer_contract.py applies.
  deploy_order: the base tables are rebuilt in full by the first build after the merge, so the
  moves reach every downstream model in that build; fct_fixture_event re-merges the affected
  matches in the same build. Nothing to sequence by hand.
  blast_radius: measured read-only on prod on 2026-10-04, the two new models run over prod's
  inputs (0.48 GB): the new test fails on 995 events in 985 player-matches today and on none
  after; 949 events move in 195 matches (801 substitutions, 49 cards, 1 goal) and 45 player rows
  in 7 matches; both tables keep their row counts (1,900,644 player rows, 868,841 events). The
  issue's table of 2026-10-03 counted 665 cases on a narrower definition (no event under the
  row's team). Player and team values change in those matches and the seasons and windows that
  hold them (cards, penalties and goals credited by team, team totals summed from players, a
  player's club in those matches); fct_fixture_event changes the team of the moved events and
  keeps the 29 events only it holds.

decisions_taken: >
  #189 as approved on 2026-10-03, and the CPO's answer in chat on 2026-10-04 to the rebuild
  question: "Self-heal, keep the 29 (Recommended)", recorded in the issue's How step 3.

  Readings, under the CPO's delegation in chat on 2026-10-02 ("Readings of approved rules are
  yours; apply the most plausible one and state it in one line"):
  - The rule is decided once, in base_apif__fixture_events, which the player model already reads;
    the events carry the decided team in resolved_player_team_id, and the player model moves its
    row from that column.
  - A player's row team is read from the provider's player rows with the same team-id overrides
    base_apif__fixture_players applies.
  - A case is a player with a row under one team of the match and at least one event under the
    other; own goals are neither evidence nor moved, as the issue's Not in scope says.
  - Where his events sit under both teams, the decided team takes all his events and his row: the
    contradicted side moves.
  - The squad list is read for the match's season in any competition; the other matches are the
    player's rows in every other match. Where neither decides, nothing moves and the test fails.
  - A moved event takes the name the match's events give its new team.

  Threshold declarations. NEW MECHANISM: none; the re-merge is the third clause of the self-heal
  fct_fixture_event already has, and the handover column is an ordinary base column. RECURRING
  COST, measured by dry run: base_apif__fixture_events reads the player rows and the squad lists,
  about 0.065 GB a night, and fct_fixture_event's nightly read grows from 0.118 GB to 0.132 GB.

decisions_reserved:
  - Own goals stay under the team they count for.
  - No catalogue, metric formula or window changes.
  - A case nothing decides is not guessed: it stays, and the test fails on it.

done_when:
  - The test, run against today's prod rows, fails on the cases; run against the new models
    inlined over prod, passes (bytes to the CPO first).
  - dbt parse, sqlfluff on the changed SQL, the offline gates and pytest pass.
  - The review cycle passes with every routed reviewer, review.md bound to --staged-hash.
  - data:build:mr is green; every changed value is compared with prod before the merge (bytes to
    the CPO first).

amendments: (none)
