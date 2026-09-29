# Task contract — #179: own goals credited to the wrong side, shoot-out kicks counted as penalties

objective: >
  Fix the open-play goal split behind Goals per shot on target. An own goal counts for the side it
  benefits (the provider files the own-goal event under the team it counts for; int_legs__team_match
  joins it as the opponent's), and shoot-out kicks (event_comments = 'Penalty Shootout') count as no
  goal and no penalty in the four readers of goal events. A new error-level test holds the split to
  the scoreline; the catalogue's descriptions state the corrected filter.

refs: >
  #179 (What exactly / Why / How). The CPO's approval of the plan in chat, and his ruling on the
  test: "A. Error, 3 named". docs/metric_layer.md.

scope_paths:
  - dbt_project/models/4_intermediate/shared/int_legs__team_match.sql
  - dbt_project/models/4_intermediate/shared/int_legs__player_match.sql
  - dbt_project/models/4_intermediate/shared/int_player_club_season__metrics.sql
  - dbt_project/models/4_intermediate/shared/int_player_season_position__metrics.sql
  - dbt_project/tests/assert_team_goal_split_adds_up_to_score.sql
  - dbt_project/seeds/metric_catalogue.csv
  - dbt_project/models/docs/metric_columns.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md
  - .claude/task/audit_reviewer_outputs.md
  - docs/tracker/**

impact_map: >
  writers: each of the four models is written only by its own SQL file (dbt `table`,
  materialisation from dbt_project.yml's 4_intermediate layer); fct_fixture_event, the one table
  they read events from, is only read here and not changed.

  downstream: `dbt ls --project-dir dbt_project --resource-type model --output name --select
  "int_legs__team_match+ int_legs__player_match+ int_player_club_season__metrics+
  int_player_season_position__metrics+"` returned 42 models: int_legs__player_match
  int_legs__team_from_players int_legs__team_match int_player_club_season__metrics
  int_player_competition_benchmarks int_player_momentum__metrics int_player_profile__contribution
  int_player_profile__yoy int_player_season__metrics int_player_season__team
  int_player_season_position__metrics int_player_season_record
  int_team_competition_benchmark_metrics_long int_team_competition_benchmarks
  int_team_momentum__metrics int_team_momentum_window int_team_profile__streaks
  int_team_profile__yoy int_team_season__deserved_vs_actual int_team_season__metrics
  int_team_season__metrics_cumulative int_team_season_record mart_competition_fixtures
  mart_competition_season_summary mart_head_to_head mart_leaderboards mart_match_days
  mart_matchday_insights mart_player_career mart_player_competition_benchmarks
  mart_player_momentum mart_player_profile mart_player_season_record
  mart_team_competition_benchmarks mart_team_fixtures mart_team_leaderboards mart_team_momentum
  mart_team_momentum_window mart_team_profile mart_team_season mart_team_season_insights
  mart_team_season_record. The columns that change are goals_own and goals_penalty on the team leg
  and goals_penalty / goals_penalty_player on the three player models; the readers of those columns
  are int_team_momentum_window, int_team_momentum__metrics, int_team_season_record,
  int_team_season__metrics_cumulative, int_player_season__metrics, mart_team_momentum and the
  player_benchmark_metrics() macro (grep of goals_own|goals_penalty over dbt_project/**/*.sql).

  layer_rules: intermediate models stay intermediate; no partition_by / cluster_by; no
  per-competition file; no materialisation override (check_layer_contract.py). league_code is not
  branched on.

  deploy_order: the four are tables rebuilt in full by every build, so the fix reaches prod at the
  first 04:00 nightly after merge with no full refresh. No incremental fact is changed. The new test
  runs in that nightly and in every MR's data build; measured against prod it is 0 rows with the
  fixed logic (52,361 matches with goal events) and 9,107 rows in 4,559 matches on today's model,
  so it must merge together with the model change, never before it.

  blast_radius: every team metric built on goals_own / goals_penalty (open-play goals, own goals,
  penalty goals, Goals per shot on target) in matches with an own goal (4,283 in fct_fixture_event)
  or a shoot-out (394), and every player metric built on the penalty count in the 394 shoot-out
  matches (open-play goals, penalty goals, Goals per shot on target, the finishing benchmark).
  Nothing else: the scoreline and player goals_total are untouched and already leave the shoot-out
  out (measured: 1,163 of 1,294 shoot-out legs match the non-shoot-out events; 10,706 of 10,713
  player rows, and none include the shoot-out).

decisions_taken: >
  The CPO approved the plan for #179 in chat: the four models as in the issue's How, the new test,
  the before/after comparison, and the catalogue wording below. His ruling on the test, chosen from
  three options: "A. Error, 3 named" — error severity, the three matches whose provider events
  disagree with the score on who scored left out by fixture id with their reasons (21650, 247587,
  1373026).

  Catalogue wording, meaning unchanged: goals_penalty and goals_penalty_player state that penalty
  shoot-out kicks are left out; goals_own says the own goals are the opponents' own goals and that
  the provider files each such event under the team it counts for. metric_columns.md is regenerated
  from the seed by scripts/sync_metric_docs_blocks.py.

  THRESHOLD DECLARATIONS: NEW MECHANISM: none — a singular dbt test, the established pattern; its
  list of three excluded fixture ids is the CPO's ruling above, and no test in dbt_project/tests has
  one today. RECURRING COST: the test reads 38,352,533 bytes per run (dry run against prod), about
  1.2 GB a month on the nightly — under one cent a month.

decisions_reserved:
  - Correcting the provider's events for the three excluded matches (they keep the provider's wrong
    split on the site): outside this task, the CPO's.
  - A player-side test for the shoot-out rule: not in #179, which names one test; the CPO's to ask for.

done_when:
  - .venv/Scripts/dbt.exe parse --project-dir dbt_project succeeds.
  - python -m sqlfluff lint on the five SQL files (repo root, jinja templater, bigquery) reports no new
    violation against main.
  - python scripts/sync_metric_docs_blocks.py --check and python scripts/check_description_hygiene.py
    pass.
  - Read-only bq, the compiled fixed int_legs__team_match inlined into the test: 0 rows; the test on
    today's prod model: red (9,107 rows); with the shoot-out filter removed and with the own-goal
    join put back on the opponent: red.
  - The fixed leg for fixture 1575150 gives Goals per shot on target 33% | 50%.
  - The validate-local gates pass; review.md binds the staged hash with every routed verdict PASS.
  - After the MR's data:build:mr: every site-facing mart in ci_mr<IID>_marts compared with prod's,
    each changed row traced to a window holding an own-goal or shoot-out match of that team or
    player, and none elsewhere; the result in the MR head.

amendments: (none)
