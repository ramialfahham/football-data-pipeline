{{ config(materialized='table') }}

{#
  Competition benchmark engine (team). Per (league_code, season_api_year, metric_key): the league
  distribution of each of the 20 team season metrics, so a team's value can be read against its peers.
  Median-led (robust to a dominant team) with the p25/p75 spread; the mean is carried for the
  "vs league average" read but is skew-sensitive. team_count is N for the rank-of-N display.

  Only teams with >= 3 finished games enter the distribution, so a 1-game team's fluky per-match rate
  cannot skew the median/percentiles. Metrics with no value for a team (e.g. player-stat coverage gaps)
  are excluded per metric (metric_value is null -> not counted).

  Window: season-to-date (W2), from int_team_season__metrics. The 20-metric list lives in
  the team_benchmark_metrics() macro (shared with mart_competition_benchmarks__team).
  Grain: (league_code, season_api_year, metric_key).
#}

with season as (
    select * from {{ ref('int_team_season__metrics') }}
    where season_games_played >= 3
),

unpivoted as (
    {% for metric_key, col in team_benchmark_metrics() %}
    select
        league_code,
        season_api_year,
        '{{ metric_key }}' as metric_key,
        {{ col }} as metric_value
    from season
    {% if not loop.last %}
    union all
    {% endif %}
    {% endfor %}
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
from unpivoted
where metric_value is not null
group by league_code, season_api_year, metric_key
