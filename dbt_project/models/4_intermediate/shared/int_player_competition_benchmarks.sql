{{ config(materialized='table') }}

{#
  Competition benchmark engine (player). Per (league_code, season_api_year, position_group, metric_key): the
  distribution of each benchmarked metric over the position's qualifying players, so a player's per-90 can be
  read against his positional peers in that competition-season. Median-led (robust) with the p25/p75 spread;
  the mean is carried for the "vs average" read but is skew-sensitive. player_count is N for the rank-of-N
  and percentile display. The player analog of int_team_competition_benchmarks.

  Only players with >= 270 minutes IN the position enter the distribution; for
  finishing_efficiency_player_pct, also >= 10 shots on target in the position (its denominator is shots, not
  minutes). Metric x position eligibility comes from player_benchmark_metrics(): a metric ineligible for
  a position (e.g. saves_player for an outfielder) yields a null value and is not counted.

  Grain: (league_code, season_api_year, position_group, metric_key). All competitions, each season on its own
  data (no league scoping, no prev-season fallback — D5/D6).
#}

with season as (
    select * from {{ ref('int_player_season_position__metrics') }}
    where minutes >= 270
),

unpivoted as (
    {% for m in player_benchmark_metrics() %}
    select
        league_code,
        season_api_year,
        position_group,
        '{{ m.key }}' as metric_key,
        case
            when
                position_group in ('{{ m.pos | join("', '") }}')
                {%- if m.floor is defined %} and {{ m.floor }}{% endif %}
                then {{ m.col }}
        end as metric_value
    from season
    {% if not loop.last %}
    union all
    {% endif %}
    {% endfor %}
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
from unpivoted
where metric_value is not null
group by league_code, season_api_year, position_group, metric_key
