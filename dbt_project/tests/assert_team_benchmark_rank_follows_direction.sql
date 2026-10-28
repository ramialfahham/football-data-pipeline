-- A team benchmark's rank 1 holds the best value by the metric's catalogue direction: the lowest
-- for a lower_better metric, the highest for every other. Returns each (league-season, metric)
-- whose rank-1 value is not that extreme.

{{ config(store_failures = true) }}

with benchmarks as (
    select
        league_code,
        season_api_year,
        metric_key,
        metric_value,
        rank
    from {{ ref('mart_team_competition_benchmarks') }}
),

catalogue as (
    select
        metric_id,
        direction
    from {{ ref('metric_catalogue') }}
    where entity = 'team'
),

per_metric as (
    select
        b.league_code,
        b.season_api_year,
        b.metric_key,
        any_value(c.direction) as direction,
        min(b.metric_value) as lowest_value,
        max(b.metric_value) as highest_value,
        min(if(b.rank = 1, b.metric_value, null)) as rank_one_value
    from benchmarks as b
    inner join catalogue as c
        on b.metric_key = c.metric_id
    group by b.league_code, b.season_api_year, b.metric_key
)

select *
from per_metric
where
    rank_one_value is null
    or rank_one_value != if(direction = 'lower_better', lowest_value, highest_value)
