# Task contract — #180: team save percentage counts an own goal as a shot the keeper failed to save

objective: >
  Team save percentage (saves_pct) becomes saves / (saves + goals conceded that were not own goals).
  The team leg gains the own goals it conceded (goals_own_against); the two same-window models sum
  them over save-covered games beside goals_against_in_save_games; the two places that divide
  subtract them; the catalogue formula and description say so.

refs: >
  #180 (What exactly / Why / How), as edited to team only. The CPO's ruling on the scope, chosen from
  three options: "B. Team now, player issue" — player save percentage is #184. The CPO's approval
  of the plan in chat. docs/metric_layer.md. The id pattern recorded on #94 (goals_own_against:
  noun goals, qualifier own, _against).

scope_paths:
  - dbt_project/models/4_intermediate/shared/int_legs__team_match.sql
  - dbt_project/models/4_intermediate/shared/int_team_momentum_window.sql
  - dbt_project/models/4_intermediate/shared/int_team_momentum__metrics.sql
  - dbt_project/models/4_intermediate/shared/int_team_season_record.sql
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season__metrics_cumulative.sql
  - dbt_project/models/5_marts/shared/mart_team_momentum.sql
  - dbt_project/models/4_intermediate/shared/int_legs.yml
  - dbt_project/models/4_intermediate/shared/int_momentum_window.yml
  - dbt_project/models/4_intermediate/shared/int_momentum.yml
  - dbt_project/models/4_intermediate/shared/int_season_record.yml
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
  writers: each changed model is written only by its own SQL file (dbt `table`); the event and
  fixture facts are only read.

  downstream: `dbt ls --project-dir dbt_project --resource-type model --output name --select
  "int_legs__team_match+"` returned 29 models: int_legs__team_match int_player_momentum__metrics
  int_player_profile__contribution int_team_competition_benchmark_metrics_long
  int_team_competition_benchmarks int_team_momentum__metrics int_team_momentum_window
  int_team_profile__streaks int_team_profile__yoy int_team_season__deserved_vs_actual
  int_team_season__metrics int_team_season__metrics_cumulative int_team_season_record
  mart_competition_fixtures mart_competition_season_summary mart_head_to_head mart_match_days
  mart_matchday_insights mart_player_momentum mart_player_profile mart_team_competition_benchmarks
  mart_team_fixtures mart_team_leaderboards mart_team_momentum mart_team_momentum_window
  mart_team_profile mart_team_season mart_team_season_insights mart_team_season_record. The new
  columns stay in intermediate models: every mart that reads int_team_momentum_window,
  int_team_momentum__metrics or int_team_season_record lists its columns, and
  int_team_season__metrics_cumulative lists its output, so no mart gains a column and the season
  drift guard sees none. saves_pct is read, unchanged in code, by int_team_profile__yoy,
  int_team_competition_benchmark_metrics_long, mart_team_season_insights, mart_team_profile,
  mart_team_season_record and mart_matchday_insights.

  layer_rules: intermediate stays intermediate; no partition_by / cluster_by; no per-competition
  file; no materialisation override (check_layer_contract.py). league_code is not branched on.

  deploy_order: all changed models are tables rebuilt in full by every build; the fix reaches prod
  at the first 04:00 nightly after merge with no full refresh. No incremental fact is changed.

  blast_radius: team saves_pct and what reads it, only for teams that conceded an own goal in the
  window or season: 4,371 of 119,674 team legs conceded an own goal, 3,897 of them with save stats
  (prod, measured). Player save percentage is untouched (#184).

decisions_taken: >
  The CPO ruled the scope ("B. Team now, player issue") and approved the plan: the new column
  goals_own_against on the team leg, its same-window sum goals_own_against_in_save_games beside the
  existing goals_against_in_save_games (which keeps its meaning), the two dividing sites, the
  catalogue formula and description (label unchanged), the column docs, no new test (#180 asks for
  none), and the before/after compared before the merge.

  THRESHOLD DECLARATIONS: NEW MECHANISM: none. RECURRING COST: none measurable — one more integer
  column carried through tables the nightly already builds.

decisions_reserved:
  - Player save percentage: #184, the CPO's to schedule.
  - The id saves_pct: renamed by #94, not here.

done_when:
  - .venv/Scripts/dbt.exe parse --project-dir dbt_project succeeds.
  - SQLFluff on the six changed SQL files (repo root, jinja templater, bigquery) reports no new
    violation against main.
  - python scripts/sync_metric_docs_blocks.py --check and python scripts/check_description_hygiene.py
    pass; the validate-local gates and pytest pass.
  - Read-only bq on the compiled fixed team leg: fixture 1575150 gives Hoffenheim goals_own_against
    1 and a match save percentage of 0.5; no saves_pct above 1 in the compiled window and season models.
  - review.md binds the staged hash with every routed verdict PASS.
  - After the MR's data:build:mr and before the merge: every site mart in ci_mr<IID>_marts compared
    with prod, each changed saves_pct traced to an own goal conceded in that team's window or season,
    the known ties of #183 reported apart; the result in the MR head.

amendments: (none)
