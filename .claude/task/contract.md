# Task contract — both stat facts rebuilt in full every night; the match-stats table shows every line the provider sent

objective: >
  Issue "A change to how base cleans player stats reaches the fact's history only through a full
  rebuild" (#188). fct_fixture_player_stats and fct_fixture_team_stats become tables rebuilt in full
  from their base every night instead of incremental merges, so a cleaning change reaches every
  match; one test fails when a fact and its base disagree on any row. base_apif__fixture_statistics
  and fct_fixture_team_stats record whether the provider sent a statistics line, and
  mart_team_fixture_stats keeps exactly those lines, a line carrying only cards included.

refs: >
  #188, edited in place on the day this contract was written with the two decisions below.
  Found in #185's team-side comparison (prod just before that merge against its MR build, by
  grain): after the merge's prod build the player fact differs from its base on 2,969 player rows
  (saves, shots, shots on target), because the merge takes only rows with a newer fetch; and 520
  provider lines carrying only cards (Europa League 302, African qualifiers 148, Conference League
  24, Champions League 22, Copa del Rey 14, Coppa Italia 6, Asian qualifiers 4) left the
  match-stats table, because its line test leaves cards out. Measured on the 3 Oct nightly: the
  player fact's merge 1.203 GB in 3 jobs, the team fact's 0.042 GB; a full player rebuild measured
  at 0.54 GB on 2 Oct (#188). Row counts equal: player fact and base 1,900,095 each, team fact and
  base 119,782 each in #185's MR build, so a rebuild from base loses no history.

acceptance_criteria:
  # Copied verbatim from the issue's checklist.
  - Both facts, `fct_fixture_player_stats` and `fct_fixture_team_stats`, are rebuilt in full every night instead of merged, so every row holds the same values as its base (`base_apif__fixture_players`, `base_apif__fixture_statistics`), the matches fetched long ago included.
  - A test fails when a fact and its base disagree on any row.
  - The match-stats table shows every statistics line the provider sent, a line with only cards included; base and the team fact record whether the provider sent a line.
  - The nightly warehouse cost before and after, measured and put to the CPO.

scope_paths:
  - dbt_project/models/2_base/api_football/base_apif__fixture_statistics.sql
  - dbt_project/models/2_base/api_football/base.yml
  - dbt_project/models/3_core/fct_fixture_player_stats.sql
  - dbt_project/models/3_core/fct_fixture_team_stats.sql
  - dbt_project/models/3_core/core.yml
  - dbt_project/models/5_marts/shared/mart_team_fixture_stats.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/models/docs/shared_columns.md
  - dbt_project/tests/assert_stat_facts_equal_base.sql
  - dbt_project/tests/assert_fct_fixture_player_stats_history_merged.sql
  - dbt_project/tests/assert_fct_fixture_team_stats_history_merged.sql
  - dbt_project/tests/assert_fanout_facts_not_empty.sql
  - dbt_project/docs/layering.md
  - scripts/diagnostics/verify_competition_ingest.py
  - .claude/skills/verify-competition-ingest/SKILL.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md
  - .claude/task/audit_reviewer_outputs.md
  - docs/tracker/**

impact_map: >
  writers: base_apif__fixture_statistics is written by its one model; fct_fixture_player_stats and
  fct_fixture_team_stats each by their one model, which selects its base one to one (keys cast,
  three columns renamed). No other model writes them.
  downstream: `dbt ls --select base_apif__fixture_statistics+ fct_fixture_player_stats+
  --resource-type model` from the repo root lists 49 models: base_apif__fixture_players
  base_apif__fixture_statistics fct_fixture_player_stats fct_fixture_team_stats
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
  mart_player_season_record mart_team_competition_benchmarks mart_team_fixture_stats
  mart_team_fixtures mart_team_leaderboards mart_team_momentum mart_team_momentum_window
  mart_team_profile mart_team_season mart_team_season_insights mart_team_season_record; and 837
  tests. Readers of the old re-merge: assert_fct_fixture_player_stats_history_merged,
  assert_fct_fixture_team_stats_history_merged (deleted here); the "incremental" wording in
  core.yml (fixture_sk of both facts), assert_fanout_facts_not_empty's header, layering.md's
  exception, and verify_competition_ingest.py's hint.
  layer_rules: check_layer_contract.py allows a per-model `incremental` only on a 3_core fact and
  no other per-model materialisation; removing the config leaves both facts on the layer default
  `3_core: +materialized: table`. fct_fixture_event keeps its incremental exception.
  deploy_order: dbt replaces an incremental table with a table when the materialisation changes;
  the post-merge build rebuilds both facts in full, then every nightly does. The mart reads
  has_stat_line from the team fact built in the same run, so there is no ordering gap.
  blast_radius: the player fact takes base's values on the 2,969 lagging player rows, and every
  player surface downstream follows (the changes #185's team-side comparison measured on its fresh
  MR build: saves filled, shots and shots on target left blank); the team fact gains
  has_stat_line and keeps its values (re-merged in full by #185's merge); mart_team_fixture_stats
  regains the 520 card-only lines. Every changed value is compared with prod by grain before the
  merge.

decisions_taken: >
  The CPO in chat on 2026-10-03, "yes to both", to these exact texts: "The match-stats table shows
  every statistics line the provider sent, a line with only cards included; base and the team fact
  record whether the provider sent a line." and "Both facts, `fct_fixture_player_stats` and
  `fct_fixture_team_stats`, are rebuilt in full every night instead of merged, and a test fails
  when a fact and its base disagree on any row."

  Readings, under the CPO's delegation in chat on 2026-10-02, "Readings of approved rules are
  yours; apply the most plausible one and state it in one line": a statistics line is a delivered
  line holding at least one value, cards included, so an all-empty block stays out as the table
  already treated it; the flag is named has_stat_line, as has_player_stats and has_team_stats are;
  the test compares every column a fact takes from its base, both ways, so a missing, extra or
  differing row fails it; fct_fixture_event keeps its incremental exception, which this decision
  does not cover.

  No new mechanism, dependency or protected path. Recurring cost: the player fact's build falls
  from a merge to a rebuild and the equality test reads both facts and both bases; measured on the
  MR build and put to the CPO with the number before the merge.

decisions_reserved:
  - A measured nightly cost that rises by more than the equality test's own read goes back to the
    CPO before the merge.
  - fct_fixture_event's materialisation stays as it is; changing it is a separate decision.

done_when:
  - dbt parse, the fast offline gates, ruff with .ruff-ci.toml, sqlfluff with the dbt templater on
    the changed models, and pytest pass.
  - The equality test, rendered against prod, returns the 2,969 lagging player rows (watched red),
    is red on a deliberate break and green on an identical rewrite; it is green on the MR build.
  - The review cycle passes with every routed reviewer, review.md bound to --staged-hash.
  - data:build:mr is green; its build is compared with prod by grain, every changed value given a
    cause, and the nightly bytes before and after measured and reported to the CPO before the merge.

amendments:
  - "+ dbt_project/models/docs/shared_columns.md: the has_stat_line doc block, one block for a
    column documented in two models, as engineering_standards.md section 2 requires."
  - "+ .claude/skills/verify-competition-ingest/SKILL.md: the skill documents
    verify_competition_ingest.py's check 3 and still told an operator to full-refresh the stale
    incremental team fact; it says what the script now says. A reader the impact map's sweep
    missed, found in review."
