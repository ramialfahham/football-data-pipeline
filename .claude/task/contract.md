# Task contract — player stats from a complete-format fetch; a newer-format match fetched again

objective: >
  The provider sends a match's player stats in one of two formats, and the newer one never carries
  goals conceded or dribbled past. Base keeps the newest fetch, so a later fetch in the newer
  format replaced complete stats (63 matches), and a match first fetched in it stays blank unless
  fetched again. Base takes a match's player rows from its newest complete-format fetch, else its
  newest fetch; ingestion fetches a match once more 14 days after kickoff while its latest fetch is
  in the newer format; a dbt test pins the result.

refs: >
  #205.

acceptance_criteria:
  - A match's player stats come from its newest fetch in the provider's complete format; a fetch in the newer format is used only while no complete one exists.
  - A match whose latest fetch is still in the newer format 14 days after kickoff is fetched once more.
  - No match with a complete-format fetch is blank for every player in goals conceded or dribbled past (a dbt test).

scope_paths:
  - dbt_project/models/2_base/api_football/base_apif__fixture_players.sql
  - dbt_project/models/2_base/api_football/base.yml
  - dbt_project/models/1_staging/api_football/stg_apif__generic.yml
  - dbt_project/tests/assert_fixture_players_from_a_complete_fetch.sql
  - ingestion/api_football/coverage.py
  - ingestion/api_football/loads/batch_fixtures.py
  - tests/test_coverage.py
  - docs/data_contract.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch

impact_map: >
  writers: RAW_APIF_FIXTURE_DETAILS is written only by ingestion/api_football/loads/batch_fixtures.py;
  coverage.read_coverage decides which finished fixtures it fetches. base_apif__fixture_players is
  the only model that picks a fetch for player stats; base_apif__fixture_events, base_apif__players
  and base_apif__teams read stg_apif__fixture_players for other purposes and are unchanged.
  downstream: `dbt ls --select base_apif__fixture_players+ --resource-type model` (repo root,
  --project-dir dbt_project): base_apif__fixture_players fct_fixture_player_stats
  int_legs__player_match int_legs__team_from_players int_player_club_season__metrics
  int_player_competition_benchmark_metrics_long int_player_competition_benchmarks
  int_player_momentum__metrics int_player_profile__contribution int_player_profile__yoy
  int_player_season__metrics int_player_season__team int_player_season_position__metrics
  int_player_season_record int_team_competition_benchmark_metrics_long
  int_team_competition_benchmarks int_team_momentum__metrics int_team_profile__yoy
  int_team_season__deserved_vs_actual int_team_season__metrics int_team_season__metrics_cumulative
  int_team_season_record mart_leaderboards mart_matchday_insights mart_player_career
  mart_player_competition_benchmarks mart_player_fixture_stats mart_player_match_log
  mart_player_momentum mart_player_profile mart_player_season_record
  mart_team_competition_benchmarks mart_team_leaderboards mart_team_momentum
  mart_team_momentum_window mart_team_profile mart_team_season mart_team_season_insights
  mart_team_season_record.
  layer_rules: base keeps first logic and picks among fetches (layering.md, 2_base); every model is
  a table set per layer (check_layer_contract.py); no league_code is hardcoded.
  deploy_order: all models are tables rebuilt in full by the nightly and the main build, so the new
  choice reaches every downstream table on the first build after merge; the ingestion change takes
  effect at the next 04:00 nightly through the redeployed image.
  blast_radius: measured on prod staging before building. 63 matches switch to an earlier
  complete-format fetch (2,654 player rows), regaining goals conceded and dribbled past. 964 rows
  in 565 matches leave base because their player is absent from the chosen fetch; 498 of them have
  minutes, and 411 of those are the same player (same team and shirt) under a second provider id
  in the chosen fetch, which base counts twice today. Answer keys: of the key matches, only Serie A
  1550091 is touched, by dropped rows; its key player 37137 is in the chosen fetch with the same 2
  saves, so no key value moves. API: 1 to 5 calls a night, about 3 on average, measured on prod
  over the next 12 nights (matches reaching 14 days in the newer format, batched per competition
  at 20 a call); none of the 406 matches whose latest fetch is in the newer format is due today,
  so there is no one-off batch. BigQuery: the coverage query now reads the players block of every
  fetch, measured 640 MB billed against 10 MB before, and it runs twice a night (orchestrator.py
  planning and completeness.py), about 1.3 GB more a night. Both approved in chat, 2026-10-06.

decisions_taken: >
  Readings, under the delegation of 2026-10-02:
  - "A match's player stats come from its newest fetch in the complete format" is a choice per
    match, not per player: every row of a match comes from that one fetch, as a match's events come
    from one fetch.
  - A fetch is in the complete format when any player in it has goals conceded, and in the newer
    format when it lists players and none has goals conceded; a payload with no players is neither,
    so a match the provider gives no player stats is not fetched again.
  - The refetch is due once: when the latest fetch is in the newer format and came under 14 days
    after kickoff, and 14 days have passed, the same shape as the 3-day second fetch.

  Threshold declarations. NEW MECHANISM: none; one more due condition in the existing coverage
  check and one dbt test. RECURRING COST: 1 to 5 API calls a night and about 1.3 GB billed a
  night for the two coverage reads, approved in chat, 2026-10-06.

decisions_reserved:
  - None.

done_when:
  - The new dbt test returns rows on prod before the change and none in the MR build.
  - The MR data build passes, answer keys included.
  - pytest (whole suite) and the offline gates pass; the coverage query's billed bytes are measured.
  - The review cycle passes, review.md bound to --staged-hash; the MR pipeline is green.
