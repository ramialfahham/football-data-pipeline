# Task contract — the Team page's comparison data, cards and highs and lows

objective: >
  The warehouse serves the comparison data of the Team page's Performance tab and its Highs and
  lows (#235, design #134). mart_team_competition_benchmarks carries every metric of the served
  list (metric_rows.json), each team's rank in its league by the metric's direction from the
  catalogue, and its value at the same point last season in a domestic league. mart_team_profile
  carries the season's card totals and the team's Highs and lows: its biggest win and heaviest
  defeat across its competitions in the season, and its longest unbeaten and winless runs in the
  competition, the runs from one intermediate the competition page's season summary reads too.
  mart_team_fixtures counts a match as upcoming only when its date has not passed. The export
  carries the last-season value and serves every club's value per metric for the strip plot on the
  featured season.

refs: >
  #235 (the build; its plan approved in chat, 2026-10-28); #134 (the Team page design, approved in
  chat, 2026-10-22 and 2026-10-28).

scope_paths:
  - dbt_project/models/4_intermediate/shared/int_team_competition_benchmark_metrics_long.sql
  - dbt_project/models/4_intermediate/shared/int_competition_benchmarks.yml
  - dbt_project/models/4_intermediate/shared/int_team_competition_benchmarks.sql
  - dbt_project/docs/layering.md
  - dbt_project/models/4_intermediate/shared/int_team_season__longest_runs.sql
  - dbt_project/models/4_intermediate/shared/int_team_season__biggest_results.sql
  - dbt_project/models/4_intermediate/shared/int_team_season_records.yml
  - dbt_project/models/5_marts/shared/mart_team_competition_benchmarks.sql
  - dbt_project/models/5_marts/shared/mart_team_profile.sql
  - dbt_project/models/5_marts/shared/mart_competition_season_summary.sql
  - dbt_project/models/5_marts/shared/mart_team_fixtures.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/seeds/metric_map.csv
  - dbt_project/tests/assert_team_benchmark_rank_follows_direction.sql
  - dbt_project/tests/assert_team_benchmark_prev_season_matches_yoy.sql
  - scripts/export_site_data.py
  - tests/test_export_site_data.py
  - tests/test_no_decision_history_in_code.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md

impact_map: >
  writers: int_team_competition_benchmark_metrics_long (14 more metrics and the value at the same
  point last season), mart_team_competition_benchmarks (rank by direction), two new intermediates
  (int_team_season__longest_runs, int_team_season__biggest_results), mart_team_profile (card
  totals, highs and lows), mart_competition_season_summary (reads the runs intermediate),
  mart_team_fixtures (the upcoming rule). downstream: `dbt ls --select
  int_team_competition_benchmark_metrics_long+ mart_team_profile+ mart_competition_season_summary+
  mart_team_fixtures+ --resource-type model` lists int_team_competition_benchmarks and the four
  marts, nothing further; the export's team payload and competition payload. layer_rules: every
  ranking and grouping is in the warehouse; the export only selects and indexes. deploy_order: the
  MR data build; the committed samples are re-exported with the page's build, which also drops the
  page's own rank turnaround (displayRank) in the same change. blast_radius: the benchmark mart's
  rank and row set, the season summary's runs (same values), the next-fixture rule on every page
  reading mart_team_fixtures.

approved_design:
  - team: #134

acceptance_criteria:
  - "mart_team_competition_benchmarks has a row per team-season for every metric of metric_rows.json the team has a value for; its rank orders by the catalogue direction (lower_better ascending, otherwise descending), ties sharing a rank; a test fails where a league-season's rank 1 is not the best value by that direction."
  - "The benchmark rows carry the value at the same point last season by rule R6, chosen as int_team_profile__yoy chooses it, null outside a domestic league; a test fails where it differs from int_team_profile__yoy's value for a metric both serve, or where a benchmark metric has no catalogue row."
  - "mart_team_profile carries cards_yellow and cards_red season totals and the highs and lows: biggest win and heaviest defeat (fixture, competition, opponent, home or away, score, kickoff) across the team's competitions in the season, and the longest unbeaten and winless runs in the competition, null below two matches; mart_competition_season_summary reads its runs from the same intermediate and its values do not change."
  - "mart_team_fixtures marks a fixture upcoming only when its status is NS or TBD and its date is today or later."
  - "The team payload's benchmark entries carry metric_value_prev_season, and the featured season carries league_strip, every club's value per metric with the team flagged; pytest pins both."

decisions_taken: >
  The build plan approved in chat, 2026-10-28, including two of its lines by name: the benchmark
  rank "follows the metric's direction from the catalogue", and mart_team_fixtures.is_upcoming
  "also checks the date, so a stale fixture never shows as next" (the date against current_date(),
  as int_team_momentum_window already does). Only the Team page reads mart_team_fixtures and the
  benchmark mart, and the committed samples it renders do not change here: the page's build
  re-exports them and drops the page's own rank turnaround in one change. Readings: the data comes in two MRs before the page
  (this one; then the Competitions block, last season's position, the last five matches and the
  squad's appearances, which need the cup-tie outcome #178 asks for), and the export of the whole
  season's fixtures follows with the page, which picks the shared rows' fields; the value at the
  same point last season sits on the benchmark rows, one row per metric, rather than as three
  columns per metric on mart_team_profile; the biggest win and heaviest defeat follow the
  competition page's rule for the biggest margin and count across the team's competitions in the
  season, as the approved mock shows; the runs follow the competition page's run rule; counts in
  the benchmark rows are cast to the float the long form holds; a neutral metric ranks high first;
  the strip plot rides on the featured season only, the one the page shows. No new dependency; the
  recurring cost is measured on the MR data build and put to the CPO before the merge.

decisions_reserved:
  - Any wording, block or rule the Team page design does not hold.

done_when:
  - dbt parse, SQLFluff on every changed model, a dry run of each against prod, pytest, the site node tests, the copy gate and the offline gates pass.
  - The MR data build passes, including the new tests; its added bytes are measured and put to the CPO.
  - Reviewers per review_routing.json pass.

amendments:
  - "2026-10-28: + dbt_project/seeds/metric_map.csv — authority: standing rule, the generated metric map must match the catalogue and the model YAML (`sync_metric_docs_blocks.py --check` in CI); content: the map rows of the new benchmark metrics and the profile's card totals, written by the generator."
  - "2026-10-28: + dbt_project/models/4_intermediate/shared/int_team_competition_benchmarks.sql and dbt_project/docs/layering.md — authority: standing rule, a repo file states only the current state; content: the header and the mart's layering row stop naming 22 metrics and a direction-agnostic rank, words removed only."
