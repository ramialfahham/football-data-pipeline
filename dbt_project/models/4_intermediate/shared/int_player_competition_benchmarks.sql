{#
  Competition benchmark engine (player). Per (league_code, season_api_year, position_group, metric_key): the
  distribution of each benchmarked metric over the position's qualifying players, so a player's per-90 can be
  read against his positional peers in that competition-season. Median-led (robust) with the p25/p75 spread;
  the mean is carried for the "vs average" read but is skew-sensitive. player_count is N for the rank-of-N
  and percentile display. The player analog of int_team_competition_benchmarks.

  Who enters the distribution, and which metrics each position is benchmarked on, is
  int_player_competition_benchmark_metrics_long.

  Grain: (league_code, season_api_year, position_group, metric_key). All competitions, each season on its own
  data (no league scoping, no prev-season fallback — D5/D6).
#}

with metrics as (
    select * from {{ ref('int_player_competition_benchmark_metrics_long') }}
)

select
    league_code,
    season_api_year,
    position_group,
    metric_key,
    count(metric_value) as player_count,
    avg(metric_value) as peer_mean,
    approx_quantiles(metric_value, 4)[offset(1)] as peer_p25,
    approx_quantiles(metric_value, 4)[offset(2)] as peer_median,
    approx_quantiles(metric_value, 4)[offset(3)] as peer_p75
from metrics
group by league_code, season_api_year, position_group, metric_key
