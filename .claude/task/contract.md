# Task contract — player side: cleaned in base, metric SQL generated from the catalogue, tests prove it

objective: >
  How step 3 of the issue "HIGH PRIORITY: the calculations are built from the catalogue's formula,
  and tests prove every metric is right". base_apif__fixture_players cleans the provider's player
  values once — accurate passes as a count for every match, the blank rule, the player-goal and
  penalty-goal source rules, the match-stat corrections with each correction recorded on its row,
  the two least() caps removed — and renames every input to our words by the approved mapping. The
  core fact re-merges itself once in the post-merge build. Every player catalogue formula reads the
  new names; the two accurate-passes rows lose the conversion. scripts/generate_metric_sql.py
  writes each player surface's metric SQL from the catalogue, its drift check a pytest in
  test:python. Tests first, pure dbt, severity error, store_failures, each shown failing on today's
  models.

refs: >
  The issue above (What exactly, How step 3, the approved input-name mapping and the rulings in its
  exploration detail, edited in place on the day this contract was written with the CPO's answers
  from chat). Measured read-only before any edit: base holds all 1,898,750 core-fact rows at the
  same version (the re-merge is lossless); the pass value per match separates count from percentage
  with no match between 1.05 and 1.5; player goals: 95,398 of 96,797 team matches add up through
  the per-player count, 448 differ only by a second provider number, 44 are genuine disagreements
  (11 checked against published match reports, the events right in 7), about 1,310 add up only
  through the events, 75 through neither; 63 player matches have more event penalty goals than
  goals. A football-analytics consultation on the cleaning readings ran before building.

acceptance_criteria:
  # Copied verbatim from the issue's checklist; this MR delivers the player side of each line.
  - A metric's numerator and denominator are written once, in `dbt_project/seeds/metric_catalogue.csv`; no model holds its own hand-written copy of a formula.
  - The models apply a window (last 5, season to date, World Cup cumulative) and the eligibility rule to that formula. A window never makes a new metric. A forfeit (AWD/WO) counts only where the league table counts it: `points_won`, `goals` and `goals_against` include it on every surface; every other metric leaves it out of numerator and denominator. Any other match with a missing input makes the metric NULL for the whole window; we never average over the matches we happen to have.
  - A blank stat is a zero only when the data shows the provider counted that stat in that match; otherwise it is missing, and the rule above makes the metric NULL. This holds alike for player stats, team totals summed from players and the team stat line. Counted means: someone else in the same match (a teammate or the other team) has a value for the stat; or nobody has, and a second source proves the zero. The score: a 0-0 means no goals, assists or goals conceded; a team that conceded none means its players conceded none. The match events: every goal of the score listed and none assisted means no assists; every goal listed and none by a player (own goals only) means no player goals; a team awarded no penalty means its players won none; a team that conceded no penalty means its players committed none; no card event means no cards. The team's own stat line: 0 shots, shots on target, saves or offsides means its players had none. A team match with no player data at all makes every player metric of that team NULL for any window that contains it: nobody knows who played or what they did.
  - Results are exact: the score, win/draw/loss, points, standings and goals, including who scored, penalty goals and own goals. A team's goals are the score. A player's goals come from the provider's per-player count or the goal events: where the two agree, or where only one adds up to the score, that one; where both add up but credit different players who both played, the events; where the events credit a player with no row in that match, the per-player count; where neither adds up, the per-player count as delivered. A player's goals are never left blank because the two sources disagree. Tests hold results at zero tolerance, apart from the matches where neither source adds up, which are counted as known exceptions.
  - Match stats are held to "good enough": shots, saves, passes, duels, tackles, dribbles, corners, fouls, cards, assists, minutes and every metric built on them. A value that contradicts a result is corrected to the nearest value consistent with it; a value that contradicts a stat vouched for by its own check in the same match is corrected to that stat; only a gap of at most 2 is corrected, and a larger gap, or a contradiction where neither side is vouched for, leaves the value blank for that match. Results are never corrected. Every correction is recorded in the cleaned table that makes it, on the corrected row (the stat, the provider's figure, ours, the rule); it is not shown on the site. A test fails the build when the share of corrected or blanked values in a competition-season exceeds its limit, set from today's measurement. This replaces the finishing-efficiency guard in the models, which checks only the window total.
  - From the core facts up, every input column is named in our own words by the ruled metric id pattern, never the provider's: base renames them by the approved mapping below, and the catalogue's formulas read only those names.
  - A test recomputes every catalogue formula from the leg tables and fails the build when a model's value differs. It covers every model and surface that computes a catalogue metric, at severity error, never warn.
  - A test checks the window and the eligibility rule: the right matches were used, and the value is NULL when any match in the window lacks an input.
  - Each new test is shown to fail when a model expression or an expected value is deliberately changed, and to stay green on an algebraically identical rewrite.

scope_paths:
  - dbt_project/models/2_base/api_football/base_apif__fixture_players.sql
  - dbt_project/models/2_base/api_football/base.yml
  - dbt_project/models/3_core/fct_fixture_player_stats.sql
  - dbt_project/models/3_core/core.yml
  - dbt_project/models/4_intermediate/shared/int_legs__player_match.sql
  - dbt_project/models/4_intermediate/shared/int_legs__team_from_players.sql
  - dbt_project/models/4_intermediate/shared/int_legs.yml
  - dbt_project/models/4_intermediate/shared/int_player_club_season__metrics.sql
  - dbt_project/models/4_intermediate/shared/int_player_club_season.yml
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_player_season__metrics.sql
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season.yml
  - dbt_project/models/4_intermediate/shared/int_player_season_position__metrics.sql
  - dbt_project/models/4_intermediate/shared/int_player_season_position.yml
  - dbt_project/models/4_intermediate/shared/int_player_momentum__metrics.sql
  - dbt_project/models/4_intermediate/shared/int_momentum.yml
  - dbt_project/models/4_intermediate/shared/int_player_season_record.sql
  - dbt_project/models/4_intermediate/shared/int_season_record.yml
  - dbt_project/models/4_intermediate/shared/int_player_profile__contribution.sql
  - dbt_project/models/4_intermediate/shared/int_player_profile__yoy.sql
  - dbt_project/models/4_intermediate/shared/int_player_profile.yml
  - dbt_project/models/5_marts/shared/mart_player_momentum.sql
  - dbt_project/models/5_marts/shared/mart_player_season_record.sql
  - dbt_project/models/5_marts/shared/mart_player_career.sql
  - dbt_project/models/5_marts/shared/mart_player_profile.sql
  - dbt_project/models/5_marts/shared/mart_player_fixture_stats.sql
  - dbt_project/models/5_marts/shared/mart_player_match_log.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/models/docs/shared_columns.md
  - dbt_project/models/docs/metric_columns.md
  - dbt_project/seeds/metric_catalogue.csv
  - dbt_project/seeds/player_match_cleaning_answer_key.csv
  - dbt_project/seeds/schema.yml
  - dbt_project/tests/assert_player_metrics_follow_catalogue_formula.sql
  - dbt_project/tests/assert_base_player_stats_cleaned.sql
  - dbt_project/tests/assert_player_match_cleaning_answer_key.sql
  - dbt_project/tests/assert_player_stat_corrections_within_limit.sql
  - dbt_project/tests/assert_fct_fixture_player_stats_history_merged.sql
  - dbt_project/tests/assert_no_uncatalogued_season_metric.sql
  - scripts/generate_metric_sql.py
  - tests/test_generate_metric_sql.py
  - tests/test_export_landing.py
  - docs/metric_layer.md
  - tests/test_no_decision_history_in_docs.py
  - .sqlfluff
  - scripts/sync_metric_docs_blocks.py
  - tests/test_sync_metric_docs_blocks.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md
  - .claude/task/audit_reviewer_outputs.md
  - docs/tracker/**

impact_map: >
  writers: base_apif__fixture_players is written only by its own SQL, from stg_apif__fixture_players
  (plus, new, base_apif__fixture_events, base_apif__fixture_statistics and base_apif__fixtures_next
  as second sources). fct_fixture_player_stats (incremental, unique_key fixture_player_stat_sk,
  on_schema_change sync_all_columns) is written only from that base model. Measured: base and fact
  hold the same 1,898,750 keys at the same raw_ingested_at.

  downstream, dbt: `.venv/Scripts/dbt.exe ls --project-dir dbt_project --select
  base_apif__fixture_players+ --resource-type model --output name` from the repo root:
  base_apif__fixture_players, fct_fixture_player_stats, int_legs__player_match,
  int_legs__team_from_players, int_player_club_season__metrics, int_player_competition_benchmarks,
  int_player_momentum__metrics, int_player_profile__contribution, int_player_profile__yoy,
  int_player_season__metrics, int_player_season__team, int_player_season_position__metrics,
  int_player_season_record, int_team_competition_benchmark_metrics_long,
  int_team_competition_benchmarks, int_team_momentum__metrics, int_team_profile__yoy,
  int_team_season__deserved_vs_actual, int_team_season__metrics,
  int_team_season__metrics_cumulative, int_team_season_record, mart_leaderboards,
  mart_matchday_insights, mart_player_career, mart_player_competition_benchmarks,
  mart_player_fixture_stats, mart_player_match_log, mart_player_momentum, mart_player_profile,
  mart_player_season_record, mart_team_competition_benchmarks, mart_team_leaderboards,
  mart_team_momentum, mart_team_momentum_window, mart_team_profile, mart_team_season,
  mart_team_season_insights, mart_team_season_record (38 models; 700 tests downstream).
  `dbt ls --select metric_catalogue+`: mart_team_leaderboards (reads direction only) and the
  catalogue guards assert_metric_catalogue_expr_resolvable, assert_no_uncatalogued_season_metric,
  assert_form_window_rates_inputs_covered, assert_season_rates_inputs_covered and the seed's own
  schema tests.

  downstream, column names: a word-boundary sweep of the 20 renamed names over models, macros,
  singular tests, seeds, scripts, tests and site_v2 found about 350 references in the dbt project
  (the core fact, the legs, six player models, two marts, the catalogue, the ymls, the doc blocks),
  none in macros, singular tests or export code. The team chain reads the player legs only through
  int_legs__team_from_players, whose inputs change name and whose output names do not (the team
  totals from players are renamed with the team side). The marts keep every column name they hand
  to the export (goals_total, goals_assists, shots_on on the momentum and season-record marts; the
  whole stat line on mart_player_fixture_stats and mart_player_match_log), so the export and the
  site read the same keys; site_v2/src reads only goals_total, goals_assists and shots_on from
  top_players.

  layer_rules: check_layer_contract.py (cleaning in base; no per-competition model; one
  materialisation rule — the core fact stays the documented incremental exception); the
  generated SQL is plain SQL in the model files, linted by sqlfluff with the full rule set.

  deploy_order: data:build:mr builds the whole chain fresh in the MR's ci_mr datasets (the fact is
  built from base, not merged), which is the "after" for the comparison with prod before the
  merge. The merge's data:build:main runs the full prod build; fct_fixture_player_stats finds prod
  without the renamed columns, so that one build processes every base row instead of only new ones
  (sync_all_columns drops the old names and adds the new, then the merge fills all 1,898,750 rows),
  and every later build is incremental as today. The schema change and the merge are separate
  statements, so a build that fails between them leaves the new columns empty; the next build finds
  goals_penalty on no row and processes every base row again, and
  assert_fct_fixture_player_stats_history_merged fails a build whose fact carries goals_penalty on
  fewer than half as many rows as base. No window with empty history, no manual prod step. The 04:00 nightly after the
  merge is an ordinary incremental run. The fact's incremental watermark is the player fetch, so a
  score corrected after a fixture's player rows are merged reaches the fact only when that fixture
  is fetched again.

  blast_radius: values change on every player surface, by the rules the issue records and measures
  (blank rule, strict rule, pass accuracy from 2020 about 0.8 instead of about 0.3, player goals
  in about 1,354 team matches, penalty goals in 63 player matches, the match-stat corrections, the
  finishing-efficiency window guard removed). Team metrics built from player totals (tackles,
  blocks, interceptions, duels, dribbles, fouls, key passes) change only where a player value is
  corrected or blanked. mart_player_fixture_stats and mart_player_match_log keep the key
  passes_accuracy_percent and carry a real percentage (accurate passes over passes) for every
  match. Every changed value is compared with prod by grain before the merge and shown to the CPO.

decisions_taken: >
  The CPO's rulings recorded in the issue: the blank rule with the strict rule for team matches with
  no player data; results exact, with the player-goal source rule (never blank over a disagreement:
  events for a genuine disagreement, the per-player count for a second provider number and where
  neither adds up); match stats good enough with corrections of at most 2, every correction
  recorded on its row in base and never shown on the site; cleaning and renaming in base by the
  approved mapping; accurate passes delivered as a count; the generator script with a pytest drift
  check; tests first. Answered in chat and not yet a written rule: penalty goals come from the
  events, never more than the player's goals, and penalties_scored is set to the same number; the
  core fact re-merges itself once in the post-merge build.

  Builder readings, applied as the most plausible football reading (the CPO asked for plausible
  choices, not a confirmation of each) and put to the football-analytics role before building:
  counted means the provider delivered a non-blank value to any player of either team in the match
  (a zero the cleaning fills in never counts), except saves and goals conceded, where a keeper's
  blank is counted only by another keeper's value; match events
  are delivered when the match has at least one substitution or card event; second-source zeros
  per team: goals conceded (0-0, or the team conceded none), assists (every team goal a penalty or
  own goal, or the match has at least one goal event with an assist name), penalties won and
  committed from in-play penalty events, cards, and the team line's shots, shots on target, saves,
  offsides (a blank in the team line is never read as 0); a blank minutes value is 0 only for a
  player with no positive value in any stat and no goal in the events (an unused substitute). A
  player the provider lists twice in one fetch keeps the row with more values, the rows' own values
  breaking a tie, so every build keeps the same row. Checks run results-anchored first, then
  part-whole: goals anchor shots on target (raised to open-play goals); the team's goals conceded
  anchor the keepers' (no player above the team's figure; the only keeper with minutes equals it
  when he played the whole match, 90 minutes or more; keepers who shared the match sum to at most
  it, and where they do not, none of them can be corrected and all are left blank under
  matched_to_team_goals_conceded); the opponent's shots on target plus its in-play missed penalties,
  when the team line passes its own check (at least the opponent's open-play goals, at most its
  shots), anchor saves; a player's assists are at most his team's goals minus his own goals (he
  cannot assist his own goal), and a team-match whose assists still add up to more than its goals
  has no single assist that can be corrected, so its positive assists are left blank under
  limited_to_team_goals; then accurate passes, completed dribbles, duels won and key passes are
  corrected down to their whole, shots are raised to shots on target, yellow cards are at most 2
  and red cards at most 1. Pass format per match: percentage when the players' values sum above
  their passes. Own goals sit on the credited team's events (the player-goal measurement adds up
  only that way). The format conversion and the blank rule's zeros are cleaning, not corrections,
  and are not recorded. The metric SQL reads the legs directly on every surface (the formula over
  the window's leg rows), so a ratio is never composed from rounded or pre-summed atoms.

  THRESHOLD DECLARATIONS. NEW MECHANISM: scripts/generate_metric_sql.py (the issue's "Decided: a
  script in scripts/ generates each surface's metric SQL from the catalogue as plain SQL in the
  model files ... a pytest in test:python fails when the SQL and the catalogue differ"), and the
  one-time full re-merge branch in fct_fixture_player_stats (the CPO's answer in chat). RECURRING
  COST: the nightly reads more (base reads the events, team statistics and fixtures; the season and
  position models read the legs instead of the club-season atoms; the cleaning test reads the
  player staging table; the fact's re-merge check reads its goals_penalty column, and
  assert_fct_fixture_player_stats_history_merged reads goals_penalty of the fact and base);
  measured on the MR's build
  against prod before the merge and put to the CPO with the number.

  Names approved by the CPO with the plan: the correction column `stat_corrections` in
  base_apif__fixture_players, one entry (stat, provider_value, value, rule) per changed value, and
  the rule names goals_from_events, penalty_goals_limited_to_goals,
  penalties_scored_matched_to_penalty_goals, raised_to_open_play_goals, raised_to_shots_on_target,
  matched_to_team_goals_conceded, limited_to_opponent_shots_on_target,
  opponent_shots_on_target_unverified, limited_to_whole, limited_to_card_maximum; a value left
  blank because the gap is over 2 carries the same rule with an empty value. Added by the CPO
  after the measurement: raised_to_part, for a whole the blank rule filled with a zero below the
  player's own delivered part (key passes with blank passes, 292 player-matches; completed dribbles
  with blank attempts, 5), where the whole is raised to the part when the gap is at most 2. Added by
  the CPO after the MR build's measurement: limited_to_team_goals, for a player's assists above his
  team's goals minus his own goals (34 player-matches, every gap at most 2; 17 of them the scorer
  also given the goal's assist, 3 from the events' goal credit), and for the positive assists of a
  team-match whose assists still add up to more than its goals (21 team-matches before the player
  check), left blank.

  The limit test, set from the measurement on the built cleaning and shown to the CPO with the
  numbers (3,186 of 1,898,750 rows corrected or blanked; per competition-season the median 0.1%,
  nine in ten under 0.5%, the highest the Copa del Rey 2023 at 7.1%, current seasons 2.2-2.6%):
  one limit for every competition-season, 8%.

decisions_reserved:
  - none: every question this step raised has been answered by the CPO and written into the issue
    or this contract.

done_when:
  - The new tests are written first and each is shown failing on today's prod models (the model
    side read from prod, the recompute side from the MR's cleaned legs where the test needs them).
  - After the build: every new and existing test passes in the MR's data:build:mr.
  - Each new test goes red on a deliberate break of a model expression or an expected value and
    stays green on an algebraically identical rewrite; the SQL and the results are shown.
  - `python scripts/generate_metric_sql.py --check` and `pytest tests/test_generate_metric_sql.py`
    pass; the pytest fails on a hand edit inside a generated block (watched red).
  - sqlfluff lints every changed model with the full rule set from the repo root; dbt parse passes;
    the offline governance gates (validate-local) pass; `python scripts/sync_metric_docs_blocks.py
    --check` passes after regenerating.
  - The MR's ci_mr build is compared with prod by grain on every player surface and the two
    match-level marts (floats at 1e-9), every changed value counted and explained, and shown to the
    CPO before he merges, with the nightly bytes before and after.
  - review.md binds the staged hash with every routed verdict PASS (scope-auditor,
    analytics-engineer, cto, platform, football-analytics).

amendments:
  - + .sqlfluff — authority: the approved plan's done_when ("sqlfluff lints every changed model with
    the full rule set"); content: large_file_skip_byte_limit raised so the cleaned base model,
    32 KB, is linted; at the default 20,000 bytes CI's `sqlfluff lint models` skips it with only a
    warning.
  - + scripts/sync_metric_docs_blocks.py, tests/test_sync_metric_docs_blocks.py — authority: the
    CPO's blank rule (issue, What exactly) and the standing rule that a statement an approved change
    makes false is part of that change; content: the generated player year-over-year sentence and
    the comment and test pinning it say a player's blank stat is a zero, so a running total never
    goes NULL for coverage; under the blank rule it does, and the player sentence gains that cause.
  - decisions_taken: the rule name raised_to_part and the limit test's level, both answered by the
    CPO in chat after the measurement.
  - decisions_taken: the rule name limited_to_team_goals, answered by the CPO in chat after the
    MR build failed player_contribution_player_pct_within_unit on a player credited with a goal
    and its assist; the reading is the issue's contradiction rule, assists being a match stat.
  - + dbt_project/tests/assert_fct_fixture_player_stats_history_merged.sql — authority: the CPO's
    answer that the core fact re-merges itself, not by his hand (decisions_taken), and the working
    agreement's §7 (every pipeline output is covered by an automated test); content: the build
    fails when the fact carries goals_penalty on fewer than half as many rows as base, so a
    re-merge that never completed cannot leave the history empty unnoticed.
