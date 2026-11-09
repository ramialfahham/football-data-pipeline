{#
  Competition benchmark engine (team). Per (league_code, season_api_year, metric_key): the league
  distribution of each team benchmark metric, so a team's value can be read against its peers.
  Median-led (robust to a dominant team) with the p25/p75 spread; the mean is carried for the
  "vs league average" read but is skew-sensitive. team_count is N for the rank-of-N display.

  Who enters the distribution is the ranking_rules doc block in models/docs/metric_rules.md. Metrics
  with no value for a team (e.g. player-stat coverage gaps) are excluded per metric (metric_value is
  null -> not counted).

  Window: season-to-date (W2). Aggregates int_team_competition_benchmark_metrics_long (the shared long
  form, also read by mart_team_competition_benchmarks, so the metric set cannot drift).
  Grain: (league_code, season_api_year, metric_key).
#}

with benchmark_metrics as (
    select * from {{ ref('int_team_competition_benchmark_metrics_long') }}
    where metric_value is not null
),

-- Exact quartiles: each is a value from the distribution, the same on every build.
quartiles as (
    select distinct
        league_code,
        season_api_year,
        metric_key,
        percentile_disc(metric_value, 0.25) over league_teams as league_p25,
        percentile_disc(metric_value, 0.5) over league_teams as league_median,
        percentile_disc(metric_value, 0.75) over league_teams as league_p75
    from benchmark_metrics
    window league_teams as (partition by league_code, season_api_year, metric_key)
),

-- The mean is summed in exact decimals, so the order of the rows cannot change it.
summary as (
    select
        league_code,
        season_api_year,
        metric_key,
        cast(avg(cast(metric_value as bignumeric)) as float64) as league_mean,
        count(metric_value) as team_count
    from benchmark_metrics
    group by league_code, season_api_year, metric_key
)

select
    s.league_code,
    s.season_api_year,
    s.metric_key,
    s.team_count,
    s.league_mean,
    q.league_p25,
    q.league_median,
    q.league_p75
from summary as s
inner join quartiles as q
    on
        s.league_code = q.league_code
        and s.season_api_year = q.season_api_year
        and s.metric_key = q.metric_key
