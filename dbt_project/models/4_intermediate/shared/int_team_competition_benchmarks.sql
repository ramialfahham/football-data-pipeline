{{ config(materialized='table') }}

{#
  Competition benchmark engine (team). Per (league_code, season_api_year, metric_key): the league
  distribution of each of the 20 team season metrics, so a team's value can be read against its peers.
  Median-led (robust to a dominant team) with the p25/p75 spread; the mean is carried for the
  "vs league average" read but is skew-sensitive. team_count is N for the rank-of-N display.

  Only teams with >= 3 finished games enter the distribution, so a 1-game team's fluky per-match rate
  cannot skew the median/percentiles. Metrics with no value for a team (e.g. player-stat coverage gaps)
  are excluded per metric (metric_value is null -> not counted).

  Window: season-to-date (W2). Aggregates int_team_competition_benchmark_metrics_long (the shared long
  form, also read by mart_team_competition_benchmarks, so the metric set cannot drift).
  Grain: (league_code, season_api_year, metric_key).
#}

with benchmark_metrics as (
    select * from {{ ref('int_team_competition_benchmark_metrics_long') }}
    where metric_value is not null
)

select
    league_code,
    season_api_year,
    metric_key,
    count(metric_value) as team_count,
    avg(metric_value) as league_mean,
    approx_quantiles(metric_value, 4)[offset(1)] as league_p25,
    approx_quantiles(metric_value, 4)[offset(2)] as league_median,
    approx_quantiles(metric_value, 4)[offset(3)] as league_p75
from benchmark_metrics
group by league_code, season_api_year, metric_key
