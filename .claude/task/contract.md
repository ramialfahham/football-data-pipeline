# Task contract — the metric answer key, the two reconciliations and the ranking floors as vars

objective: >
  #185 How step 5, which closes #185 and #192. Two reconciliation tests at severity error: a
  team-season equals the provider's league table (wins, draws, losses, goals, goals against; our
  points equal the table's 3 x wins + draws), and a team-season's goals, less its forfeit goals,
  equal its players' goals plus its own goals. An answer key: real team-seasons and player-seasons,
  each catalogue metric's numerator and denominator worked out by hand from the provider's raw
  match data, committed as two seeds, and two tests that the season surfaces return exactly them.
  The player benchmark metric set moves from the player_benchmark_metrics() macro into a model, as
  the team side's is, and each ranking floor becomes a dbt var read by every model that applies it,
  held equal to the ranking_rules words by a pytest.

refs: >
  #185 (How step 5 and its checklist), #192, approved by the CPO; the step 5 line carries his
  answer of 2026-10-04 on the floors and the nightly cost. The CPO's go to build it as its own MR,
  2026-10-05.

acceptance_criteria:
  # #185's checklist lines this step closes, and #192's What exactly, verbatim.
  - "For a sample of real team-seasons and players across leagues, including a World Cup window, the expected value is worked out by hand from the raw provider data, committed as a seed, and a test asserts the pipeline returns exactly it."
  - "Independent reconciliations fail the build on disagreement: a team's goals equal the sum of its players' goals; goals for, goals against and points equal the provider's league table."
  - "Each new test is shown to fail when a model expression or an expected value is deliberately changed, and to stay green on an algebraically identical rewrite."
  - "The nightly warehouse cost is measured before and after and put to the CPO."
  - "A test that fails when a team's points in the provider's league table (`fct_standings` / `mart_standings`, `points`) differ from `points_won` summed over the team's finished matches in the same competition-season and table section."

scope_paths:
  - dbt_project/dbt_project.yml
  - dbt_project/macros/player_benchmark_metrics.sql
  - dbt_project/models/4_intermediate/shared/int_player_competition_benchmark_metrics_long.sql
  - dbt_project/models/4_intermediate/shared/int_player_competition_benchmarks.sql
  - dbt_project/models/4_intermediate/shared/int_team_competition_benchmark_metrics_long.sql
  - dbt_project/models/4_intermediate/shared/int_competition_benchmarks.yml
  - dbt_project/models/4_intermediate/shared/int_player_season_position__metrics.sql
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season__deserved_vs_actual.sql
  - dbt_project/models/5_marts/shared/mart_leaderboards.sql
  - dbt_project/models/5_marts/shared/mart_player_competition_benchmarks.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/seeds/team_season_answer_key.csv
  - dbt_project/seeds/player_season_answer_key.csv
  - dbt_project/seeds/schema.yml
  - dbt_project/tests/assert_team_season_equals_league_table.sql
  - dbt_project/tests/assert_team_goals_equal_players_goals.sql
  - dbt_project/tests/assert_team_season_answer_key.sql
  - dbt_project/tests/assert_player_season_answer_key.sql
  - dbt_project/docs/engineering_standards.md
  - dbt_project/docs/layering.md
  - docs/wireframes/12_player_stats.md
  - tests/test_ranking_floors.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md
  - .claude/task/audit_reviewer_outputs.md
  - docs/tracker/**

impact_map: >
  writers: every changed model is written only by itself and rebuilt in full each night (no
  incremental model is touched). The new int_player_competition_benchmark_metrics_long is written
  only by itself. The two new seeds are loaded by dbt seed / dbt build and read only by the two
  answer-key tests. The four new tests read int_team_season__metrics, int_player_season__metrics,
  int_player_club_season__metrics, int_legs__team_match, int_legs__player_match, fct_standings and
  the two seeds, and write only their store_failures tables.
  downstream, `dbt ls --project-dir dbt_project --resource-type model --select
  int_player_competition_benchmarks+ mart_player_competition_benchmarks+
  int_team_competition_benchmark_metrics_long+ int_team_season__deserved_vs_actual+
  mart_leaderboards+` (8 models): int_player_competition_benchmarks
  int_team_competition_benchmark_metrics_long int_team_competition_benchmarks
  int_team_season__deserved_vs_actual mart_leaderboards mart_player_competition_benchmarks
  mart_team_competition_benchmarks mart_team_profile. The new model sits between
  int_player_season_position__metrics and those two player benchmark models. The macro has no
  other reader (`git grep player_benchmark_metrics`: the two models, three descriptions and the
  wireframe 12_player_stats.md:146 that names it as the set's home).
  layer_rules: the metric set and eligibility move into an intermediate model (layering.md:
  feature engineering that does not belong in a consumption model); no model sets its own
  materialisation; check_layer_contract.py applies. A var is read with var(), as
  active_competition_league_codes and event_loss_detector_from are.
  deploy_order: dbt build orders the new model before its two readers and loads the seeds before
  the tests that read them; the first build after the merge rebuilds the 8 models in one pass.
  Nothing to sequence by hand.
  blast_radius: none intended. The vars carry today's numbers (270, 10, 3) and the new model holds
  today's metric set, eligibility and floors, so every value of the 8 models stays the same; shown
  by comparing the MR's CI build with prod, table by table on its grain, before the merge. The
  tests change no model. Measured read-only on prod on 2026-10-05: the league-table check returns
  0 rows over 2,724 table rows with the same games played; the goals reconciliation 0 rows over
  5,116 comparable team-seasons; the answer key agrees on all 180 team and 230 player values.

decisions_taken: >
  #185 step 5 as written, and its step 5 line's answer of 2026-10-04: each floor is a dbt var in
  dbt_project.yml, read by every model that applies it, with a section 1.3 paragraph and a pytest
  holding the ranking_rules words equal to the vars; the nightly cost is accepted.

  Readings, under the CPO's delegation of 2026-10-02 ("Readings of approved rules are yours"):
  - League table: compared only where the table's played equals our season_games_played, on every
    table section of the team-season; points as 3 x the table's wins + draws, since a deduction or a
    halving is the table's own adjustment (#192's How), and the table's points never above that or
    blank, the one direction no deduction explains (measured 0 rows on 2026-10-05). Antwerp BPL 2024 (41 matches with the
    Conference League play-off final, the table 40) is not compared by that rule. No exception list.
  - Goals: compared where both sides are known (players' goals known for every club-season row of
    the team, the team's own goals known). A team-season holding a team-match whose players' goals
    plus own goals miss the score is the issue's known exception, left out;
    assert_base_player_stats_cleaned (goals_do_not_add_up) already fails any such match where
    either source adds up, so every exception is one where neither does.
  - Answer key: one seed for team-seasons and one for player-seasons, a row per (entity,
    competition-season, catalogue metric on the surface) with the numerator and denominator as
    integers and the hand working; the test compares safe_divide of them with the model value
    exactly, a blank numerator meaning the value must be blank. Asserted on int_team_season__metrics
    and int_player_season__metrics. Worked out from RAW_APIF_FIXTURE_DETAILS and the
    fixture_result_corrections seed only, by the catalogue formulas and the cleaning rules, never
    from a model. The sample: World Cup 2026 Spain and Argentina, EURO 2024 Spain, Bundesliga
    2024-25 Union Berlin (an awarded match), Premier League 2024-25 Liverpool (six saves corrected);
    players World Cup 2026 Mbappe and E. Martinez (keeper), EURO 2024 Dani Olmo, Premier League
    2024-25 Salah, Bundesliga 2024-25 Kane.
  - Floors: the three numbers the issue names are vars: player_min_minutes 270,
    player_min_shots_on_target 10, team_min_matches 3. The team ranking's "from its first finished
    match" is a team having a season row, not a floor.
  - The player benchmark model mirrors the team one: int_player_competition_benchmark_metrics_long,
    one row per (player_sk, season_sk, position_group, metric_key) with value, numerator and
    denominator, eligibility and floors applied; the engine aggregates it and the mart ranks it.
  - The wireframe line that names the macro as the set's home names the model instead; what the
    screen shows does not change.

  Threshold declarations. NEW MECHANISM: none; dbt vars, seeds of hand-worked answers, singular
  tests and an intermediate model are all existing patterns, and the vars were approved in the step
  5 line. RECURRING COST: four tests and one small model in the nightly build, measured by dry run
  and put to the CPO with the MR.

decisions_reserved:
  - No catalogue row, formula, window or display changes.
  - No result or table value is changed; a red row in the league-table check would be researched
    and corrected in the correction seeds under cleaning_rules, a separate change.
  - docs/metric_layer.md, engineering_standards.md sections 2 and 3 and the catalogue's rule text in
    seeds/schema.yml stay #190's; this change adds only the two new seeds' descriptions.

done_when:
  - Each new dbt test, compiled and run over prod (bytes to the CPO first), returns no row today;
    each fails on a deliberate break of a model expression or of an expected value, and stays green
    on an algebraically identical rewrite.
  - The pytest fails when a var and the ranking_rules words disagree, or a floor is written as a
    literal in a model.
  - dbt parse, sqlfluff on the changed SQL, the offline gates and pytest pass.
  - The review cycle passes with every routed reviewer, review.md bound to --staged-hash.
  - data:build:mr is green; the 8 changed models of the CI build equal prod on their grain (bytes
    to the CPO first); the nightly cost added is measured.

amendments:
  - 2026-10-05: + dbt_project/docs/layering.md — authority: the CPO's go to build #185 step 5 as its
    own MR (2026-10-05); content: the mart_player_competition_benchmarks row names the new long model
    it composes and drops its copy of the minutes floor, which the var and ranking_rules now hold.
    The league-table check also fails on table points above 3 x wins + draws or blank (#192's How:
    the direction comes from the measurement). No product, metric or display change.
