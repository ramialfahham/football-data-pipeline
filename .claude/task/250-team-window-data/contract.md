# Task contract — Team page redesign: the warehouse

objective: >
  Issue #250, the approved Team page design: the warehouse serves a club's season across all its
  competitions (the six This season cards, and every comparison metric this season against the
  whole of last season), and each international club competition's benchmarks over its league
  or group phase only, so the page's "Compared with other teams" ranks a club among that phase's
  teams. The page, the export and the docs are a second MR.

refs: >
  #250, the design approved in chat, 2026-11-06, on the mock in EN, DE and FI; its 5 Nov note lists
  this data. The season rule is the Player page's, int_competition_season__club_windows. Plan and
  model names ruled by the coordinating session on 2026-11-10.

scope_paths:
  - dbt_project/models/4_intermediate/shared/int_team__featured_season.sql
  - dbt_project/models/4_intermediate/shared/int_team_window__metrics.sql
  - dbt_project/models/4_intermediate/shared/int_team_competition_phase__metrics.sql
  - dbt_project/models/4_intermediate/shared/int_team_competition_benchmark_metrics_long.sql
  - dbt_project/models/4_intermediate/shared/int_team_profile.yml
  - dbt_project/models/4_intermediate/shared/int_competition_benchmarks.yml
  - dbt_project/models/5_marts/shared/mart_team_page_window_metrics.sql
  - dbt_project/models/5_marts/shared/mart_team_profile.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/seeds/team_window_answer_key.csv
  - dbt_project/seeds/schema.yml
  - dbt_project/seeds/metric_map.csv
  - dbt_project/models/docs/metric_columns.md
  - dbt_project/docs/layering.md
  - dbt_project/tests/assert_team_window_answer_key.sql
  - dbt_project/tests/assert_team_benchmark_international_pool_is_the_league_phase.sql
  - dbt_project/tests/assert_team_page_window_rates_inputs_covered.sql
  - dbt_project/tests/assert_team_metrics_follow_catalogue_formula.sql
  - dbt_project/docs/engineering_standards.md
  - tests/test_no_decision_history_in_code.py
  - scripts/generate_metric_sql.py
  - .claude/task/250-team-window-data/contract.md
  - .claude/task/250-team-window-data/review.md
  - .claude/task/250-team-window-data/review_input.patch

impact_map: >
  writers: dbt only; no ingestion change. One new seed, team_window_answer_key, read by one test.
  New models: int_team__featured_season, int_team_window__metrics,
  int_team_competition_phase__metrics, mart_team_page_window_metrics.
  Changed: int_team_competition_benchmark_metrics_long (an international club competition's rows
  read the phase model), mart_team_profile (is_featured_season read from int_team__featured_season,
  same rule, same column).
  lineage: `dbt ls --resource-type model --select int_team_competition_benchmark_metrics_long+`
  returns int_team_competition_benchmark_metrics_long int_team_competition_benchmarks
  mart_team_competition_benchmarks. `dbt ls --resource-type model --select mart_team_profile+`
  returns mart_player_index mart_team_index mart_team_profile.
  consumption: export_site_data.py reads mart_team_competition_benchmarks whole and mart_team_profile
  with select *; the page reads benchmarks for the featured season only (export gate
  `is_featured_season`), which is never an international club competition while the club has a
  domestic league season. No export reads the new mart before the page MR.
  ci_layer_rules: scripts/check_layer_contract.py (no mart ref from intermediate, the any_value /
  approx_quantiles ban), scripts/check_description_hygiene.py,
  scripts/check_relationships_coverage.py, tests/test_generate_metric_sql.py (the generated blocks).
  deploy_order: one merge; the nightly builds the new models. No backfill.
  blast_radius: mart_team_competition_benchmarks rows of international club competition-seasons with
  a league or group phase (UCL, UEL, UECL, AFCCL, LIBER, CAFCL 2025, CWC 2025) change to that phase's
  teams and matches: values, ranks, team_count and the distribution. Measured on prod, UCL 2026
  pools 81 teams with any match against 36 in the league phase. Domestic leagues, domestic cups,
  knockout-only competitions and national-team competitions are unchanged. 883 clubs' pages open on
  an international competition (no domestic league season); on today's page 372 of them show a
  comparison, and after this MR 196 do, with the phase's values: the other 176 played no league or
  group phase match that season, which the approved design's filter also leaves without one. The
  site deploy is manual, so a page shows this only after the next deploy. mart_team_profile's
  is_featured_season changes only where two seasons of one year tied and the pick was arbitrary; it
  now follows the latest match. Measured on prod, 86 teams move, none with a domestic league
  season. Four new tables.

approved_design:
  - none: no page surface file changes; the data today's Team page reads changes as blast_radius states

decisions_taken: >
  The season of the window is the Player page's rule: this_season is every club competition-season
  of the featured season (int_competition_season__club_windows), last_season every one of the
  season before, leaving out those already in this_season; the window is anchored at the team's
  featured season, the rule mart_team_profile already applies, lifted unchanged into
  int_team__featured_season so both read one copy, with a tie-break it lacked: seasons of one year
  stand in the order of their latest match, then by league_code: the Player page's rule for its
  featured season (int_player__page_profile), so both pages pick the same way (ruled by the
  coordinating session on 2026-11-10).
  Matches, wins, goals and goals against count a forfeit as the league table does (rules R3, R7);
  every other value is the catalogue formula, blank when any match lacks an input (R4). Matches
  and wins are counts of results, no catalogue metrics, so the mart holds them as columns and the
  four other cards as metric_key rows. The window model's grain (team_sk, window_type) leaves
  room for a national team's window; this MR builds the club windows only, while the national-team
  question is with the CPO. A league or group phase is a round whose round_stage_kind is table
  (int_round_names); an international club competition is a club competition other than a
  domestic league or domestic cup. mart_team_page_window_metrics is a new mart: the existing
  mart_team_window_metrics is per fixture, and the per-competition marts would break grain.
  Names ruled by the coordinating session. No new mechanism. Recurring cost: four small tables in
  the nightly build, about 0.15 GB a day by dry-run, against about 129 GB a day today.

decisions_reserved:
  - What a national team's Team page shows in This season and the comparisons: with the CPO through
    the coordinating session; not built here.

done_when:
  - dbt parse succeeds from the repo root.
  - python scripts/generate_metric_sql.py --check passes.
  - python scripts/check_layer_contract.py, check_description_hygiene.py and
    check_relationships_coverage.py pass.
  - python -m pytest tests -q is green.
  - SQLFluff adds no violation on any changed model or test.
  - CI's data:build:mr is green, assert_team_window_answer_key and
    assert_team_benchmark_international_pool_is_the_league_phase included.
  - The ci_mr tables are compared with prod read-only - mart_team_profile differs only in
    is_featured_season for the tied teams blast_radius counts, mart_team_competition_benchmarks
    differs only on international club competition-seasons with a table phase, and UCL 2026 has
    36 teams there.

amendments:
  - 2026-11-10: + dbt_project/docs/layering.md, dbt_project/seeds/metric_map.csv,
    dbt_project/models/docs/metric_columns.md — authority: standing rule that a new or changed mart
    is listed in layering.md's mart table and in the generated metric map in the same MR
    (scope-auditor and tests/test_metric_map.py, round 1); content: the new mart's row, the
    benchmarks row's league or group phase, and the regenerated map.
  - 2026-11-10: + dbt_project/tests/assert_team_page_window_rates_inputs_covered.sql,
    dbt_project/docs/engineering_standards.md — authority: engineering_standards.md section 3.2,
    one rate guard and range tests per window surface (analytics-engineer-reviewer, round 4);
    content: the guard over the two new surfaces, its name in the section's list of guards, and
    range tests on the three new tables.
  - 2026-11-10: + dbt_project/tests/assert_team_metrics_follow_catalogue_formula.sql — authority:
    engineering_standards.md section 3.2, one definition per rate bound by a test
    (analytics-engineer-reviewer, round 5); content: the two new surfaces in the recompute's list,
    each with its window rebuilt from the legs.
  - 2026-11-10: + tests/test_no_decision_history_in_code.py — authority: the standing rule that a pin
    moves only down, and is lowered in the change that lowers it; content: PINNED_LINES 282 to
    281, after mart_team_profile's featured-season comment lost its issue reference.
