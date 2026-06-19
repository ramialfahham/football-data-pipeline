# Review — feat/mart-competition-benchmarks — 2026-06-19

> PR-b of the team competition-benchmark build: the benchmark engine + mart. Extends
> int_team_season__full_season_metrics with 4 catalogued metrics (clean_sheets rate +
> tackles/interceptions/blocks per match); adds int_competition_benchmarks__team (per-metric league
> distribution) + mart_competition_benchmarks__team (LONG: value · median/mean/p25/p75 · rank k-of-N ·
> vs-median), over the 20 team metrics, season-to-date, teams with >= 3 games. Median-led, rank not
> percentile, direction-agnostic (catalogue direction joined at display). Mart-only, no export wiring;
> benchmark-first (#500 rename deferred). Required reviewers (dbt_project/** + always): scope-auditor +
> analytics-engineer-reviewer — both PASS.

diff_sha256: f66f0d79fdadd9a021634486bccda819a09810afae4a2401e638451514eeae7d

## scope-auditor
VERDICT: PASS
risks_checked:
- Scope containment + no silent §10: every edit is within scope_paths (no export/script touched); the 20-metric set, median+rank-not-percentile, direction-agnostic, >=3 floor, clean_sheets-as-rate, benchmark-first were all worked out + CPO-agreed this conversation and the diff matches them; no new metric definition (the 4 added int columns are already-catalogued team metric_ids); the benchmark is transparent stats (median/mean/percentiles/rank), NOT a fabricated composite index (no Appendix-A invented score).
- Benchmark-first / #500 honored + deferred scope kept out: int_team_season__full_season_metrics is EXTENDED additively but NOT renamed (no #500 consolidation pulled in); shot_share/points_capture are not benchmarked (reserved to deserved-vs-actual), dribbles excluded (#510), player benchmark + percentile + opponent-context reserved to v1.x. The >=3 floor is a CPO-reserved "flag-don't-block" check — verified consistent in the engine + the mart.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Fan-out on clean_sheets_count_season: int_legs__team_match and int_legs__team_from_players are both grain (fixture_sk, team_sk), so the LEFT JOIN is 1:1 — countif(goals_against = 0) is an exact clean-sheet count with no inflation; clean_sheets_season = count / season_games_played is bounded 0-1 (now in the ratio range test) over the same game set; tackles/interceptions/blocks per match divide the existing sums by player_stat_coverage_season_games (the same-window rule). All 4 are catalogued team metric_ids — the no-drift guard still passes.
- Rank/distribution population symmetry + the rank test: the engine and mart both apply season_games_played >= 3 then filter metric_value is not null; the mart's inner join on (league_code, season_api_year, metric_key) restricts rank rows to the distribution population, so rank ∈ [1, team_count] (BigQuery RANK()'s max equals N even with ties) — the rank between 1 and team_count test is sound. approx_quantiles(metric_value, 4) is exact at N~18; count(metric_value) skips nulls so team_count matches the ranked set. Grains unique; metric_value renamed off the reserved word; SELECT columns == documented shared.yml columns; view materialization correct.

## escalations
(none)
