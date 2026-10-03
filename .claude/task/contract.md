# Task contract — team side: cleaned in base, forfeits by the rule, team metric SQL generated from the catalogue, tests prove it

objective: >
  How step 4 of the issue "HIGH PRIORITY: the calculations are built from the catalogue's formula,
  and tests prove every metric is right". base_apif__fixture_statistics cleans the team line once,
  for every team in every finished match: the blank rule, penalty and own goals read from the events,
  the contradiction rule with each correction recorded on its row, the inputs renamed by the approved
  mapping. fct_fixture_team_stats re-merges itself once in the post-merge build.
  int_legs__team_match only joins; int_legs__team_from_players is renamed and follows the blank
  rule. Every team catalogue formula reads the new names. scripts/generate_metric_sql.py writes the
  season and form-window team metric SQL from the catalogue, a forfeit counted only in points, goals
  and goals against. Tests first, pure dbt, severity error, store_failures, each shown failing on
  today's models.

refs: >
  The issue above: What exactly, How step 4, the approved input-name mapping, and the section "Step
  4: how each rule reads on the team side, and what it changes" in its exploration detail, edited in
  place on the day this contract was written from the plan the CPO approved in chat. Measured
  read-only before any edit, on 1 Oct data: team-line blanks per stat (red cards blank on 70,934 of
  100,292 lines, the other team's value counting 106 of them; yellow 3,104; saves 2,212; every other
  stat blank on both sides or not at all); 8,496 of 119,660 played team legs without a substitution
  or card event, 6,412 of them scoring; 178 team-matches whose goal events do not add up to the
  score; video-review cancelled goals already absent (4,383 of 4,384 team-matches with one add up as
  delivered); whole-team blank totals from players (blocks 7,510, tackles 6,564, duels 3,468
  team-matches). The football-analytics role is consulted on the cleaning readings before building.
  Out of scope by the CPO's choice in the same conversation: the qualifying-campaign form window
  ("Form-window code diverges from metrics_context_model.md section 4 in two places").

acceptance_criteria:
  # Copied verbatim from the issue's checklist; this MR delivers the team side of each line.
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
  - dbt_project/models/2_base/api_football/base_apif__fixture_statistics.sql
  - dbt_project/models/2_base/api_football/base_apif__fixture_players.sql
  - dbt_project/models/2_base/api_football/base.yml
  - dbt_project/models/3_core/fct_fixture_team_stats.sql
  - dbt_project/models/3_core/core.yml
  - dbt_project/models/4_intermediate/shared/int_legs__team_match.sql
  - dbt_project/models/4_intermediate/shared/int_legs__team_from_players.sql
  - dbt_project/models/4_intermediate/shared/int_legs.yml
  - dbt_project/models/4_intermediate/shared/int_team_season_record.sql
  - dbt_project/models/4_intermediate/shared/int_season_record.yml
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season__metrics_cumulative.sql
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season__metrics.sql
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season__deserved_vs_actual.sql
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season.yml
  - dbt_project/models/4_intermediate/shared/int_team_momentum_window.sql
  - dbt_project/models/4_intermediate/shared/int_team_momentum__metrics.sql
  - dbt_project/models/4_intermediate/shared/int_momentum.yml
  - dbt_project/models/4_intermediate/shared/int_momentum_window.yml
  - dbt_project/models/4_intermediate/shared/int_team_profile__yoy.sql
  - dbt_project/models/4_intermediate/shared/int_team_profile__streaks.sql
  - dbt_project/models/4_intermediate/shared/int_team_profile.yml
  - dbt_project/models/4_intermediate/shared/int_player_profile__contribution.sql
  - dbt_project/models/4_intermediate/shared/int_player_profile.yml
  - dbt_project/models/4_intermediate/shared/int_team_competition_benchmark_metrics_long.sql
  - dbt_project/models/4_intermediate/shared/int_team_competition_benchmarks.sql
  - dbt_project/models/4_intermediate/shared/int_competition_benchmarks.yml
  - dbt_project/models/5_marts/shared/mart_team_momentum.sql
  - dbt_project/models/5_marts/shared/mart_team_momentum_window.sql
  - dbt_project/models/5_marts/shared/mart_team_season.sql
  - dbt_project/models/5_marts/shared/mart_team_season_record.sql
  - dbt_project/models/5_marts/shared/mart_team_profile.sql
  - dbt_project/models/5_marts/shared/mart_team_fixtures.sql
  - dbt_project/models/5_marts/shared/mart_head_to_head.sql
  - dbt_project/models/5_marts/shared/mart_competition_season_summary.sql
  - dbt_project/models/5_marts/shared/mart_team_fixture_stats.sql
  - dbt_project/models/5_marts/shared/mart_team_leaderboards.sql
  - dbt_project/models/5_marts/shared/mart_team_competition_benchmarks.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/models/5_marts/domestic_league/mart_team_season_insights.sql
  - dbt_project/models/5_marts/domestic_league/mart_matchday_insights.sql
  - dbt_project/models/5_marts/domestic_league/domestic_league.yml
  - dbt_project/models/docs/shared_columns.md
  - dbt_project/models/docs/metric_columns.md
  - dbt_project/seeds/metric_catalogue.csv
  - dbt_project/seeds/team_match_cleaning_answer_key.csv
  - dbt_project/seeds/schema.yml
  - dbt_project/tests/assert_team_metrics_follow_catalogue_formula.sql
  - dbt_project/tests/assert_base_team_stats_cleaned.sql
  - dbt_project/tests/assert_team_match_cleaning_answer_key.sql
  - dbt_project/tests/assert_team_stat_corrections_within_limit.sql
  - dbt_project/tests/assert_fct_fixture_team_stats_history_merged.sql
  - dbt_project/tests/assert_team_form_window_follows_the_rule.sql
  - dbt_project/tests/assert_team_yoy_pairs_the_same_games_played.sql
  - dbt_project/tests/assert_team_goal_split_adds_up_to_score.sql
  - dbt_project/tests/assert_season_rates_inputs_covered.sql
  - dbt_project/tests/assert_form_window_rates_inputs_covered.sql
  - dbt_project/tests/assert_awarded_matches_do_not_null_team_stats.sql
  - dbt_project/tests/assert_momentum_awarded_matches_do_not_null_team_stats.sql
  - dbt_project/tests/assert_mart_team_season_insights_metric_consistency.sql
  - dbt_project/tests/assert_no_uncatalogued_season_metric.sql
  - dbt_project/tests/assert_base_player_stats_cleaned.sql
  - dbt_project/tests/assert_team_season_games_not_short_of_standings.sql
  - dbt_project/tests/assert_tournament_form_window.sql
  - dbt_project/tests/assert_metric_catalogue_expr_resolvable.sql
  - scripts/generate_metric_sql.py
  - tests/test_generate_metric_sql.py
  - scripts/sync_metric_docs_blocks.py
  - tests/test_sync_metric_docs_blocks.py
  - scripts/declare_missing_columns.py
  - docs/metric_layer.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md
  - .claude/task/audit_reviewer_outputs.md
  - docs/tracker/**

impact_map: >
  writers: base_apif__fixture_statistics is written only by its own SQL, today from
  stg_apif__fixture_statistics, base_apif__fixtures_next (participants) and the
  fixture_team_id_overrides seed; it adds base_apif__fixture_events (the goal split, the card zeros,
  missed penalties) and the finished fixtures of base_apif__fixtures_next (the score, and one row per
  team per finished match). fct_fixture_team_stats (incremental, unique_key fixture_team_stat_sk,
  on_schema_change sync_all_columns) is written only from that base model. Neither event model
  changes.

  downstream, dbt: `.venv/Scripts/dbt.exe ls --project-dir dbt_project --select
  base_apif__fixture_statistics+ int_legs__team_from_players+ --resource-type model --output name`
  from the repo root: base_apif__fixture_players, base_apif__fixture_statistics,
  fct_fixture_player_stats, fct_fixture_team_stats, int_legs__player_match,
  int_legs__team_from_players, int_legs__team_match, int_player_club_season__metrics,
  int_player_competition_benchmarks, int_player_momentum__metrics, int_player_profile__contribution,
  int_player_profile__yoy, int_player_season__metrics, int_player_season__team,
  int_player_season_position__metrics, int_player_season_record,
  int_team_competition_benchmark_metrics_long, int_team_competition_benchmarks,
  int_team_momentum__metrics, int_team_momentum_window, int_team_profile__streaks,
  int_team_profile__yoy, int_team_season__deserved_vs_actual, int_team_season__metrics,
  int_team_season__metrics_cumulative, int_team_season_record, mart_competition_fixtures,
  mart_competition_season_summary, mart_head_to_head, mart_leaderboards, mart_match_days,
  mart_matchday_insights, mart_player_career, mart_player_competition_benchmarks,
  mart_player_fixture_stats, mart_player_match_log, mart_player_momentum, mart_player_profile,
  mart_player_season_record, mart_team_competition_benchmarks, mart_team_fixture_stats,
  mart_team_fixtures, mart_team_leaderboards, mart_team_momentum, mart_team_momentum_window,
  mart_team_profile, mart_team_season, mart_team_season_insights, mart_team_season_record
  (49 models; 848 tests downstream). `dbt ls --select metric_catalogue+`: mart_team_leaderboards
  (reads direction only) and the catalogue guards (assert_metric_catalogue_expr_resolvable,
  assert_no_uncatalogued_season_metric, assert_form_window_rates_inputs_covered,
  assert_season_rates_inputs_covered, assert_player_metrics_follow_catalogue_formula, the seed's
  own schema tests).

  downstream, readers by name (a read-only sweep): the team-line names are read by
  int_legs__team_match, mart_team_fixture_stats (which hands every one to the export's matchstats
  files, read by no site page), base_apif__fixture_players (team_lines) and
  assert_base_player_stats_cleaned; core.yml and shared.yml declare them. goals_for and the
  opponent_* names of int_legs__team_match are read by int_team_season_record,
  int_team_momentum_window, int_team_profile__streaks, int_player_profile__contribution,
  mart_team_fixtures, mart_head_to_head, mart_competition_season_summary and
  assert_team_goal_split_adds_up_to_score. key_passes and duels_total of
  int_legs__team_from_players are read by int_team_season_record and int_team_momentum__metrics.
  The season model's *_sum_season columns are read by int_team_season__metrics,
  int_team_season__deserved_vs_actual, int_team_profile__yoy, mart_team_season,
  mart_team_season_record, mart_team_season_insights and two singular tests; int_team_season_record
  is read only by int_team_season__metrics_cumulative and assert_season_rates_inputs_covered;
  int_team_momentum__metrics only by mart_team_momentum. The marts keep every column name they hand
  to the export (goals_for on mart_team_fixtures, mart_head_to_head, mart_team_momentum_window,
  mart_team_season, mart_team_profile, mart_team_season_insights; the stat line on
  mart_team_fixture_stats), so the export and the site read the same keys; site_v2/src reads
  goals_for (TeamFixtureRow, RecentMatch, HeadToHead) and catalogue metric ids, no team-line name.

  layer_rules: check_layer_contract.py (cleaning in base; base reads only stg_* and base_*; no
  per-competition model; one materialisation rule, the core fact the documented incremental
  exception); the generated SQL is plain SQL in the model files, linted by sqlfluff with the full
  rule set; check_yml_vs_projection.py holds the yml declarations to the model output.

  deploy_order: data:build:mr builds the whole chain fresh in the MR's ci_mr datasets (the fact is
  built from base, not merged), which is the "after" for the comparison with prod before the merge.
  The merge's data:build:main runs the full prod build; fct_fixture_team_stats finds prod without
  the renamed columns, so that one build processes every base row instead of only new ones
  (sync_all_columns drops the old names and adds the new, then the merge fills every row), and every
  later build is incremental. A build that fails between the schema change and the merge leaves the
  new columns empty; the next build finds them on no row and processes every base row again, and
  assert_fct_fixture_team_stats_history_merged fails a build whose fact holds shots on fewer than
  half as many rows as base. The fact's watermark becomes the newest of the stat line's, the events' and
  the fixture's fetch, so a later fetch of any of them re-merges that row. No manual prod step; the
  04:00 nightly after the merge is an ordinary incremental run.

  blast_radius: values change on every team surface, by the readings the issue records and
  measures: blank cards and saves; penalty and own goals blank where the events cannot prove them
  (open-play goals, penalty goals, own goals, finishing efficiency and save % NULL for any window
  holding one; the legs without events alone touch 3,258 of 13,911 team-seasons); the team-line
  corrections; whole-team blank totals from players now missing; forfeits out of every per-match
  rate, clean sheets and the goal splits; deserved points over played matches. Player values change
  only where a player zero rests on a team-line value the cleaning changed. fct_fixture_team_stats
  gains a row for every team in a finished match without a stat line; mart_team_fixture_stats keeps
  only the lines the provider delivered. Every changed value is compared with prod by grain and
  given a cause before the CPO merges.

decisions_taken: >
  Pre-approved by the plan the CPO approved in chat on the day this contract was written, whose text
  is the issue's How step 4 and its "Step 4" exploration section, both edited into the issue the
  same day. Each reading below is stated once there; this contract applies it, it does not restate
  it differently.

  Where the cleaning lives: base_apif__fixture_statistics holds one row per team per finished match,
  with or without a stat line, so the goal split is cleaned in base for team-matches with events and
  no line; int_legs__team_match only joins; the event models stay as delivered and only base reads
  the provider's event wording. The blank rule (counts only: possession, a share, stays blank), the
  goal split, the contradiction checks (shots on target raised to the open-play goals and shots to
  at least both; saves lowered to the opponent's shots on target plus its missed penalties where
  that figure passes its own check, blank where it fails; shots inside the box lowered to the total;
  inside the box lowered by the own goals credited to the team where the split exceeds the total by
  exactly them, the provider's convention up to 2018; any other split of shots that does not add up
  blanked, apart from shots on target; a gap of at most 2 corrected, a larger one blank), each
  correction in stat_corrections on its row as for players; the corrections limit 20% of a
  competition-season's lines, over competition-seasons of at least 20 lines. Team totals from
  players blank where any player row is blank. Forfeits counted only in points_won, goals and
  goals_against; they keep their place in the form window, matches played and W/D/L; deserved points
  fitted on played matches, scaled by them, its gap against the points from played matches; a
  player's share of his club's goals leaves the club's forfeit goals out. The season surface (int_team_season__metrics_cumulative,
  every matchday; int_team_season__metrics its last row) and the form window
  (int_team_momentum__metrics; mart_team_momentum only selects) generated from the catalogue;
  intermediate columns take the catalogue ids, the marts keep the names the site reads;
  mart_team_fixture_stats keeps passes_accuracy_percent, computed from accurate passes over passes as
  the player marts do. base_apif__fixture_players reads the cleaned team line. docs/metric_layer.md
  states the team side as built.

  The mechanism is the one the issue decided for players (a script in scripts/ writing plain SQL
  between marker lines, its drift check a pytest in test:python); extending it to the team surfaces
  is not a new mechanism. Threshold declaration, recurring cost: the new tests and the reshaped
  surfaces change the nightly's bytes; they are measured on the MR's build and put to the CPO with
  the number before the merge, as the issue's checklist requires. No new dependency, no protected
  path, no new warehouse object class.

decisions_reserved:
  - A reading whose measured effect on the MR's build differs materially from the effect the issue
    records (for example far more blanked windows than measured) goes back to the CPO with the
    numbers before the merge; it is never adjusted silently.
  - Any metric id, label, format or catalogue definition beyond the input renames of the approved
    mapping is out of scope and escalated, never changed here.
  - The qualifying-campaign form window stays out, as the CPO chose; the window test names it.

done_when:
  - python scripts/generate_metric_sql.py --check exits 0, and pytest tests/test_generate_metric_sql.py
    tests/test_sync_metric_docs_blocks.py passes, with a team surface hand-edited inside its block
    shown to fail the check.
  - The fast offline gates pass (.claude/hooks/stop_gate.py FAST_GATES, validate-local): dbt parse,
    check_layer_contract.py, check_yml_vs_projection.py, sync_metric_docs_blocks.py --check,
    check_description_hygiene.py, ruff with .ruff-ci.toml, sqlfluff lint of every changed model
    from the repo root with the full rule set.
  - Every new test, rendered outside dbt against prod's relations, returns rows on today's models
    (watched red) and none on the new models inlined over prod's tables; each is shown red on a
    deliberate break and green on an algebraically identical rewrite. Every query dry-run first,
    its bytes shown to the CPO.
  - The answer-key cases are worked by hand from the raw rows and the base model returns exactly
    them.
  - The review cycle passes with every routed reviewer, review.md bound to --staged-hash.
  - data:build:mr is green; the MR's ci_mr build is compared with prod by grain, every changed
    value given a cause with the counts reconciled per column, and the nightly bytes of the new
    tests and models measured and reported to the CPO before the merge.

amendments:
  - "+ dbt_project/models/4_intermediate/shared/int_momentum_window.yml: the yml of
    int_team_momentum_window, already in scope, declaring the columns the approved mapping renames.
    Authority: the plan the CPO approved, How step 4 (the inputs renamed by the approved mapping).
    The deploy_order line now states the history test's threshold as the test file has it."
  - "decisions_taken restates the readings the build settled, each measured and edited into the
    issue's Step 4 section the same day: the own-goal correction of the box split, shots held to
    the open-play goals, possession outside the blank rule, the corrections limit and its 20-line
    floor, and the forfeit goals left out of a player's share. Authority: the plan the CPO approved;
    readings of approved rules are the builder's, stated in one line each."
  - "The readings above (the own-goal correction of the box split, shots held to the open-play
    goals, possession outside the blank rule, the corrections limit of 20% and its 20-line floor
    as the limit the issue sets from today's measurement) are the builder's under the CPO's
    delegation, in chat on 2026-10-02: \"Readings of approved rules are yours; apply the most
    plausible one and state it in one line.\""
  - "contribution_player_pct leaves the club's forfeit goals out of its denominator, and its
    catalogue description and the team_goals_season doc block say so (the goals the club scored
    on the pitch). Authority: the issue's What exactly line 2, verbatim: \"A forfeit (AWD/WO) counts only where the league
    table counts it: `points_won`, `goals` and `goals_against` include it on every surface; every
    other metric leaves it out of numerator and denominator.\""
  - "Descriptions say what a thing means on cleaned data. In metric_catalogue.csv the null
    conditions, coverage caveats and provider notes come out of the description column, and
    deserved_points and deserved_points_gap say played matches, as the model computes; the
    seeds/schema.yml doc of that column, the generated models/docs/metric_columns.md, and the yml,
    doc blocks and model headers this branch touched lose their restatements of the cleaning, blank
    and forfeit rules, which live in docs/metric_layer.md and the code. Authority, the CPO in chat
    on 2026-10-02: \"Rewrite every catalogue description yourself: what the metric means, on cleaned data, in
    plain words; no caveats, null conditions, display notes, history, provider trivia or jargon.\"
    This supersedes decisions_reserved line 2 for the description column only; ids, labels,
    formats and formulas change only by the approved input renames. The full rewrite of every
    description is its own issue."
  - "base_apif__fixture_players and assert_base_player_stats_cleaned judge a keeper's saves
    against the opponent's shots and shots on target as delivered, before the team cleaning's own
    corrections, as base_apif__fixture_statistics judges them; proven zeros still come from the
    cleaned team line. Found by the MR build: assert_player_match_cleaning_answer_key failed on
    fixture 1550091, where the team cleaning raised the opponent's 1 shot on target to its 2
    open-play goals and the raised figure then passed the check the delivered one fails; both
    answer keys leave those saves blank. Authority: What exactly line 5, \"a contradiction where
    neither side is vouched for, leaves the value blank\", read as the team side reads it, under
    the CPO's delegation quoted above."
