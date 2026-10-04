# Task contract — a result that differs from the league's official decision is corrected to it, with its source

objective: >
  The issue "A result that differs from the league's official decision is corrected to it, with
  its source" (#194). Eight match results the provider files wrongly are corrected to the league's
  official decision, and the provider's league-table rows that the research finds wrong are
  corrected the same way: two seeds of hand corrections, each row naming its source, applied once
  in base_apif__fixtures_next and base_apif__standings with the provider's values kept on the row.
  A test fails when a correction is not applied, has no valid source, or no longer changes
  anything. The cleaning_rules doc block states the rule.

refs: >
  #194, approved by the CPO on 2026-10-04; its research items edited into it the same day.

acceptance_criteria:
  # The issue's checklist lines, verbatim.
  - "These 8 matches carry the official result in every table and on the site; the provider's value stays next to ours in the cleaned table: Union Berlin-Bochum, BL1 14 Dec 2024: 1-1 -> 0-2 awarded; Bastia-Lyon, L1 16 Apr 2017: 0-0 -> 0-0 awarded to Lyon (the LFP set no score: Lyon gets the win, no goals); Sassuolo-Pescara, SA 28 Aug 2016: 0-3 as played -> 0-3 awarded; Al Orubah-Al Nassr, SPL 28 Feb 2025: 2-1 -> 0-3 awarded; Istanbulspor-Trabzonspor, TSL 19 Dec 2023: 1-2 -> 0-3 awarded; Galatasaray-Adana Demirspor, TSL 9 Feb 2025: 1-0 -> 3-0 awarded; Antwerp-Beerschot, BPL 29 Sep 2024: 4-0 -> 5-0 awarded; Seongnam-Ulsan, KL1 4 Sep 2022: 3-0 -> 2-0"
  - "Every provider league-table row the research finds wrong shows the league's figures (at least Sassuolo 46 and Pescara 18, Serie A 2016-17; the ranks of Sampdoria and Cagliari follow)."
  - "An awarded match counts like every forfeit (R3): in points, goals and goals against, in no other metric."
  - "Each correction names its source: the league's or federation's decision, or two independent match reports."
  - "A check fails when a correction no longer changes anything."
  - "`cleaning_rules` says: a result is corrected only to the league's official decision, with its source; match stats never correct a result."

scope_paths:
  - dbt_project/seeds/fixture_result_corrections.csv
  - dbt_project/seeds/standings_corrections.csv
  - dbt_project/seeds/schema.yml
  - dbt_project/models/2_base/api_football/base_apif__fixtures_next.sql
  - dbt_project/models/2_base/api_football/base_apif__standings.sql
  - dbt_project/models/2_base/api_football/base.yml
  - dbt_project/models/3_core/fct_fixture.sql
  - dbt_project/models/3_core/core.yml
  - dbt_project/models/4_intermediate/shared/int_legs__team_match.sql
  - dbt_project/models/docs/cleaning_rules.md
  - dbt_project/models/docs/shared_columns.md
  - dbt_project/tests/assert_result_corrections_applied.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/models/5_marts/shared/mart_standings.sql
  - dbt_project/docs/layering.md
  - docs/content_architecture.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md
  - .claude/task/audit_reviewer_outputs.md
  - docs/tracker/**

impact_map: >
  writers: base_apif__fixtures_next and base_apif__standings are each written only by their own
  model, rebuilt in full every night; fct_fixture and int_legs__team_match likewise. The two new
  seeds are loaded by dbt seed / dbt build and read only by the two base models and the new test.
  downstream, `dbt ls --project-dir dbt_project --select base_apif__fixtures_next+
  base_apif__standings+ --resource-type model` (69 models, 29 marts): base_apif__fixture_events
  base_apif__fixture_players base_apif__fixture_statistics base_apif__fixtures_next
  base_apif__players base_apif__standings base_apif__teams base_apif__teams_global dim_player
  dim_player_team_season_mapping dim_team dim_team_competition_season_mapping fct_fixture
  fct_fixture_event fct_fixture_player_stats fct_fixture_team_stats fct_standings
  int_legs__player_match int_legs__team_from_players int_legs__team_match
  int_player_club_season__metrics int_player_competition_benchmarks int_player_momentum__metrics
  int_player_profile__contribution int_player_profile__yoy int_player_season__metrics
  int_player_season__team int_player_season_position__metrics int_player_season_record
  int_team_competition_benchmark_metrics_long int_team_competition_benchmarks
  int_team_momentum__metrics int_team_momentum_window int_team_profile__streaks
  int_team_profile__yoy int_team_season__deserved_vs_actual int_team_season__metrics
  int_team_season__metrics_cumulative int_team_season__standings_primary int_team_season_record
  mart_competition_fixtures mart_competition_index mart_competition_season_summary
  mart_fixture_standing_context mart_head_to_head mart_leaderboards mart_match_days
  mart_matchday_insights mart_next_matchday mart_player_career mart_player_competition_benchmarks
  mart_player_fixture_stats mart_player_match_log mart_player_momentum mart_player_profile
  mart_player_season_record mart_roster mart_standings mart_team_competition_benchmarks
  mart_team_fixture_stats mart_team_fixtures mart_team_leaderboards mart_team_market_value
  mart_team_momentum mart_team_momentum_window mart_team_profile mart_team_season
  mart_team_season_insights mart_team_season_record. base_apif__standings+ alone is 13 of them
  (fct_standings, int_team_season__standings_primary, int_team_season__deserved_vs_actual and the
  marts reading the table). fct_fixture_event reads base_apif__fixtures_next for team ids only.
  layer_rules: the corrections are applied in base, which may read staging and seeds; core and
  intermediate only carry the corrected columns; no model sets its materialisation and no new
  model is added; check_layer_contract.py applies. The win/draw/loss stays decided once, in
  int_legs__team_match.
  deploy_order: dbt build loads the seeds before the models that read them, so the first build
  after the merge applies every correction in one pass; every changed model is rebuilt in full.
  fct_fixture_event is incremental and reads no changed column. Nothing to sequence by hand.
  blast_radius: measured read-only on prod on 2026-10-04 (0.14 GB). 8 fixtures change: the score in
  6 (Union Berlin-Bochum, Al Orubah-Al Nassr, Istanbulspor-Trabzonspor, Galatasaray-Adana
  Demirspor, Antwerp-Beerschot, Seongnam-Ulsan), the status to AWD in 7 (all but Seongnam-Ulsan),
  the winner in 1 (Bastia-Lyon). 16 team-seasons change W/D/L, goals, goals against or points;
  after the change all 16 equal the provider's table on W, D, L and goals except Sassuolo and
  Pescara, whose table rows are the ones corrected, and points differ only by the table's
  deductions (Istanbulspor, Adana Demirspor). 4 table rows change, Serie A 2016-17: Sassuolo and
  Pescara (the provider kept the 2-1) and the ranks of Sampdoria and Cagliari. The 232 player rows
  of the 6 awarded matches with player data leave every player surface (they read FT/AET/PEN
  only); the team stat lines of the awarded matches leave every team metric (is_awarded_result)
  and stay on the match page unchanged. Seongnam's goal events list the 37' goal twice, so with
  the score at 2-0 they no longer add up and its penalty and own goals in that match, and its KL1
  2022 goal split, go blank under the Results rule. Downstream: points, goals, goals against,
  W/D/L counts, form, streaks, head-to-head, season summaries, standings and rank on the pages
  of those teams and seasons.

decisions_taken: >
  #194 as approved on 2026-10-04, under the rule cleaning_rules already states: results are exact.

  The research items of its step 2, settled by research and edited into the issue: Bastia-Lyon
  was lost by Bastia with no score set (the LFP imposed none; both tables count the match with no
  goals), recorded 0-0 with the win to Lyon; Antwerp's two table rows already count the 5-0
  (regular season 47 = 46 + 1; Championship Round 57 = 47 + 10 play-off goals) and Beerschot's
  Relegation Round row counts it too, so none of them is corrected.

  Readings, under the CPO's delegation of 2026-10-02 ("Readings of approved rules are yours"):
  - A match the league awarded without setting a score carries its winner in the seed
    (awarded_to_team_id), passed from base through fct_fixture to int_legs__team_match, which
    decides every win, draw and loss; elsewhere the score decides, as today.
  - An awarded correction sets status_short to AWD and status_long to 'Technical loss', the
    provider's own pair for an awarded match, so every rule keyed on an awarded result applies;
    Seongnam-Ulsan was played and keeps FT.
  - The provider's goals and status stay on every row of base_apif__fixtures_next
    (provider_goals_home, provider_goals_away, provider_status_short); result_correction_source
    names the source on a corrected row and is NULL elsewhere.
  - A table row is corrected in full (rank, played, W, D, L, goals for and against, points); its
    goal difference follows from the corrected goals; the provider's figures stay on the row as
    provider_*; result_correction_source names the source. The rank is a figure of the row, so
    Sampdoria's and Cagliari's rows, ranked below the provider's 49 for Sassuolo, are corrected.
  - Sourced: source_kind official (the league's or federation's decision, record or table) needs
    at least one https URL; match_reports needs at least two on different hosts.
  - Still needed: a match correction changes the provider's goals or status or sets a winner the
    score does not show; a table correction changes at least one of the provider's figures.
  - The stat lines of the awarded matches are cleaned as every awarded match's is today; measured,
    no shown team stat changes. R3's text stays as it is.

  Threshold declarations. NEW MECHANISM: none; a seed of hand corrections applied in base is the
  pattern of fixture_team_id_overrides, and the new columns are ordinary columns. RECURRING COST:
  two seeds of a few rows, two joins in base and one test, measured by dry run before the commit.

decisions_reserved:
  - How the site marks an awarded match does not change: it shows the score and the result, as
    for every awarded match today.
  - No catalogue row, metric formula or window changes.
  - Match stats and events are not corrected (the issue's Not in scope).

done_when:
  - The test, run against today's prod rows, fails on every correction; run against the new models
    inlined over prod, passes (bytes to the CPO first).
  - dbt parse, sqlfluff on the changed SQL, the offline gates and pytest pass.
  - The review cycle passes with every routed reviewer, review.md bound to --staged-hash.
  - data:build:mr is green; every changed value is compared with prod before the merge (bytes to
    the CPO first).

amendments:
  - 2026-10-04: + dbt_project/models/5_marts/shared/shared.yml, mart_standings.sql,
    dbt_project/docs/layering.md, docs/content_architecture.md — authority: the CPO's go to build
    #194 as its own MR (2026-10-04); content: the texts that call every standings value the
    provider's row as published now say the provider's row, corrected to the league's official
    figures where they differ; the base, core and mart column texts the same. No product, metric
    or display change.
