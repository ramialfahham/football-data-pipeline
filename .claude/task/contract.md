# Task contract — #177, part 1: the form window serves every Form comparison metric

objective: >
  mart_team_momentum serves, per team over its form window, every metric the next match page's
  Form comparison shows: 16 more, each a catalogue row with its formula and label_i18n_key, its
  inputs carried from the team line and the player feed. No name, no translation, no site change.

refs: >
  #177 (the metric catalogue), its match-page part first, the order and the build approved in chat,
  2026-10-07; #166 "Form comparison rows" (the 40-metric list, approved in chat, 2026-10-07).

scope_paths:
  - dbt_project/models/2_base/api_football/base_apif__fixture_statistics.sql
  - dbt_project/models/2_base/api_football/*.yml
  - dbt_project/models/3_core/fct_fixture_team_stats.sql
  - dbt_project/models/3_core/*.yml
  - dbt_project/models/4_intermediate/shared/int_legs__team_match.sql
  - dbt_project/models/4_intermediate/shared/int_team_momentum_window.sql
  - dbt_project/models/4_intermediate/shared/int_team_momentum__metrics.sql
  - dbt_project/models/4_intermediate/shared/*.yml
  - dbt_project/models/5_marts/shared/mart_team_momentum.sql
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season__metrics_cumulative.sql
  - dbt_project/models/4_intermediate/shared/int_team_season_record.sql
  - dbt_project/models/4_intermediate/domestic_league/team_season/*.yml
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/models/5_marts/domestic_league/*.yml
  - dbt_project/models/docs/metric_columns.md
  - dbt_project/models/docs/cleaning_rules.md
  - dbt_project/seeds/metric_catalogue.csv
  - dbt_project/seeds/metric_map.csv
  - dbt_project/tests/assert_team_metrics_follow_catalogue_formula.sql
  - dbt_project/tests/assert_base_team_stats_cleaned.sql
  - dbt_project/tests/assert_stat_facts_equal_base.sql
  - scripts/generate_metric_sql.py
  - tests/test_generate_metric_sql.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/audit_reviewer_outputs.md

impact_map: >
  writers: each changed model is written only by itself (dbt); the catalogue seed by hand, the
    generated metric block by scripts/generate_metric_sql.py, metric_columns.md and metric_map.csv
    by scripts/sync_metric_docs_blocks.py.
  downstream: `dbt ls --resource-type model --select base_apif__fixture_statistics+ --output name`
    → base_apif__fixture_players base_apif__fixture_statistics fct_fixture_player_stats
    fct_fixture_team_stats int_legs__player_match int_legs__team_from_players int_legs__team_match
    int_player_club_season__metrics int_player_competition_benchmark_metrics_long
    int_player_competition_benchmarks int_player_momentum__metrics int_player_profile__contribution
    int_player_profile__yoy int_player_season__metrics int_player_season__team
    int_player_season_position__metrics int_player_season_record
    int_team_competition_benchmark_metrics_long int_team_competition_benchmarks
    int_team_momentum__metrics int_team_momentum_window int_team_profile__streaks
    int_team_profile__yoy int_team_season__deserved_vs_actual int_team_season__metrics
    int_team_season__metrics_cumulative int_team_season_record mart_competition_fixtures
    mart_competition_season_summary mart_head_to_head mart_leaderboards mart_match_days
    mart_matchday_insights mart_player_career mart_player_competition_benchmarks
    mart_player_fixture_stats mart_player_match_log mart_player_momentum mart_player_profile
    mart_player_season_record mart_team_competition_benchmarks mart_team_fixture_stats
    mart_team_fixtures mart_team_leaderboards mart_team_momentum mart_team_momentum_window
    mart_team_profile mart_team_season mart_team_season_insights mart_team_season_record (51).
    Every change is an added column; no existing column's expression changes, so no existing value
    moves (measured: mart_team_momentum 9,042 and int_team_season__metrics_cumulative 120,030
    rows, 0 differing from prod). int_team_season__metrics gains the 15 season columns through
    `select *`; mart_team_momentum_window and every other mart select named columns and gain
    nothing.
  layer_rules: base pivots and cleans (the existing blank rule applied to free kicks); core
    carries; intermediate legs and window carry inputs; the metric math is generated from the
    catalogue; the mart selects. league_code stays the discriminator; check_layer_contract.py and
    the materialisation rule unchanged.
  deploy_order: additive columns, built by the nightly after merge. The export copies every
    column of mart_team_momentum into each side's w1 in the fixture files, so the next manual deploy
    export writes the 16 new keys there (about 1.3 KB per file); the site reads none until the page
    build.
  blast_radius: mart_team_momentum gains 16 columns; int_legs__team_match and the form window gain
    input columns; base and core gain free_kicks. Existing columns unchanged.

decisions_taken: >
  The 40-metric list and the build order are approved in chat, 2026-10-07. Metric ids follow the
  ruled pattern, input then calculation (<input>_per_match, <input>_pct, <input>_share_pct for a
  share of both teams' totals, as shots_share_pct): possession's id is passes_share_pct. The 15
  new rows' label_en, description, interpretation, direction and tier, as committed, are approved
  in chat, 2026-10-07, shown as exact text; label_en is the approved name with the catalogue's Ø or
  % prefix, displayed nowhere, and is removed with the column by a later #177 MR. Fouls and offsides come
  from the provider's team line, as cards and corners do. Possession is own passes over both
  teams' passes, summed over the window (#177). Free kicks takes the blank rule every count takes;
  it does not decide has_stat_line. A window metric is blank when any of its matches lacks the
  input (rule R4): free kicks reaches 1,732 of 11,954 team lines this season, measured 2026-10-07,
  so it is blank in most windows and the page leaves the row out where neither side has it.

  THRESHOLD DECLARATIONS: NEW MECHANISM: none (catalogue rows through the existing generator).
  RECURRING COST: the nightly read before and after, measured by dry run and put to the CPO before
  merge.

decisions_reserved:
  - The displayed names of the new metrics (strings.ts EN, DE, FI): put to the CPO with the page
    build.
  - The other surfaces of #177 (team page, Rankings, Home): their own MRs.

done_when:
  - python scripts/generate_metric_sql.py and python scripts/sync_metric_docs_blocks.py --check
    clean; pytest tests/ passes.
  - dbt parse clean; SQLFluff clean on every changed model.
  - Compiled SQL inlined against prod, read-only: every existing mart_team_momentum column equal
    before and after; the new columns equal the catalogue formula recomputed by hand for two teams.
  - The nightly bytes before and after, measured by dry run, put to the CPO.
  - data:build:mr green.

amendments:
  - 2026-10-07: + the season chain (int_team_season_record, which carries the season's inputs,
    int_team_season__metrics_cumulative and the team-season and
    domestic-league mart ymls) — authority: CPO in chat, 2026-10-07, after the rule that every team
    metric is on the season surface (tests/test_generate_metric_sql.py) put the 16 metrics there;
    content: the season tables gain the 16 columns, existing values unchanged, the extra nightly
    bytes measured before merge.
  - 2026-10-07: + dbt_project/tests/assert_base_team_stats_cleaned.sql and
    dbt_project/tests/assert_stat_facts_equal_base.sql — authority: CPO in chat, 2026-10-07;
    content: free_kicks joins each test's column list, so its blank rule and its carry into core
    are tested like every other count.
