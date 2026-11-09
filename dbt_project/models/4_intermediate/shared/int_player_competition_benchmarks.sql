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
),

-- Exact quartiles: each is a value from the distribution, the same on every build.
quartiles as (
    select distinct
        league_code,
        season_api_year,
        position_group,
        metric_key,
        percentile_disc(metric_value, 0.25) over peers as peer_p25,
        percentile_disc(metric_value, 0.5) over peers as peer_median,
        percentile_disc(metric_value, 0.75) over peers as peer_p75
    from metrics
    where metric_value is not null
    window peers as (partition by league_code, season_api_year, position_group, metric_key)
),

-- The mean is summed in exact decimals, so the order of the rows cannot change it.
summary as (
    select
        league_code,
        season_api_year,
        position_group,
        metric_key,
        cast(avg(cast(metric_value as bignumeric)) as float64) as peer_mean,
        count(metric_value) as player_count
    from metrics
    group by league_code, season_api_year, position_group, metric_key
)

select
    s.league_code,
    s.season_api_year,
    s.position_group,
    s.metric_key,
    s.player_count,
    s.peer_mean,
    q.peer_p25,
    q.peer_median,
    q.peer_p75
from summary as s
left join quartiles as q
    on
        s.league_code = q.league_code
        and s.season_api_year = q.season_api_year
        and s.position_group = q.position_group
        and s.metric_key = q.metric_key
