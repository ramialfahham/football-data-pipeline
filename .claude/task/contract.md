# Task contract — feat: mart_competition_benchmarks__team (the benchmark engine, PR-b)

> PR-b of the team competition-benchmark build (CPO-directed 2026-06-19). Build the team-vs-league
> benchmark over the 20 team season metrics: median-led, rank-of-N (no percentile), neutral/positional
> (the catalogue's direction is joined at display). Builds on PR-a's direction/interpretation (#511).
> CPO chose benchmark-first; the #500 team-season rename/consolidation comes later (the 4 metric
> additions here are additive and survive that rename).

objective: >
  Add the team competition benchmark. (1) Extend int_team_season__full_season_metrics with the 4 metrics
  it lacks (clean_sheets rate, tackles/interceptions/blocks per match — their sums already exist there).
  (2) int_competition_benchmarks__team: per (league_code, season, metric_key) league distribution over the
  20 benchmark metrics (league_median, league_mean, p25, p75, team_count), over teams with >= 3 games.
  (3) mart_competition_benchmarks__team: LONG, one row per (team_sk, season_sk, metric_key) — value,
  league_median/mean/p25/p75, rank (k of N), vs_median_delta. Direction-agnostic (positional). A macro
  holds the 20-metric list shared by the intermediate + mart.

refs: team competition-benchmark design (this conversation); PR-a = #511 (direction/interpretation); shot_share/points_capture reserved to deserved-vs-actual; #500 = the later team-season rename/consolidation.

scope_paths:
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season__full_season_metrics.sql
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season.yml
  - dbt_project/macros/team_benchmark_metrics.sql
  - dbt_project/models/4_intermediate/shared/int_competition_benchmarks__team.sql
  - dbt_project/models/4_intermediate/shared/int_competition_benchmarks.yml
  - dbt_project/models/5_marts/shared/mart_competition_benchmarks__team.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/docs/layering.md
  - .claude/task/contract.md
  - .claude/task/review.md

decisions_taken: >
  CPO-directed (2026-06-19): team benchmark over the 20 metrics (the locked display set minus the
  deserved-vs-actual inputs shot_share/points_capture, the non-metrics league_rank/points_won, and the
  retiring dribbles). Median-led + rank-of-N (NOT percentile — counter-intuitive at N~18); neutral by
  default (the mart carries no direction — that lives in the catalogue, joined at display); rank = RANK
  over value desc within (league, season, metric_key), stated as k of team_count. >= 3 games floor to
  enter the distribution (avoids a 1-game team's fluky rate skewing the median; my recommendation, kept
  on "go ahead"). clean_sheets is benchmarked as the RATE (clean-sheet games / games) — the comparable
  scalar (the "x/y" count display stays on mart_team_season). Mart-only, NO export wiring (the
  vs-benchmark block is in PAUSED #391, same as mart_roster). Benchmark-first; #500 rename later.

decisions_reserved:
  - Player benchmark + percentile-vs-peers = v1.x (a separate build).
  - The opponent/schedule-context flagship (which weights opponents via this engine) = v1.x.
  - #500 team-season rename/consolidation = a separate later PR; do NOT rename int_team_season__full_season_metrics here.
  - If the >= 3 floor proves wrong at review, it is a one-line change — flag, do not block.
  - No new metric definitions; the 4 added int columns are already catalogued team metrics (drift-clean).

done_when:
  - int_team_season__full_season_metrics computes clean_sheets (rate), tackles/interceptions/blocks per
    match; the no-drift guard still passes (all 4 are catalogued team metric_ids); int_team_season.yml
    documents them (clean_sheets joins the 0-1 ratio range test).
  - int_competition_benchmarks__team grain (league_code, season_api_year, metric_key); metric_key
    accepted_values = the 20 ids; team_count >= 1; median/p25/p75 present.
  - mart_competition_benchmarks__team grain (team_sk, season_sk, metric_key); rank between 1 and
    team_count; relationships team_sk -> dim_team, season_sk -> dim_competition_season; metric_key
    accepted_values = the 20 ids; vs_median_delta = value - league_median.
  - dbt parse clean; sqlfluff lint passes on the new SQL; layering.md lists both new models.
  - reviewers: scope-auditor + analytics-engineer-reviewer PASS (>=2 risks each); no FAIL; no ESCALATE.

amendments: (none)
