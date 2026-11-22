-- A player board of a competition-season is served only when every finished match of it has player
-- statistics (the ranking_rules doc block). Returns a row (= fails) for each competition-season with
-- season boards that has a finished match without a player line of any minutes.
{{ config(store_failures = true) }}

with served as (
    select distinct season_sk
    from {{ ref('mart_leaderboards') }}
    where window_type = 'season_to_date'
),

with_stats as (
    select fixture_sk
    from {{ ref('fct_fixture_player_stats') }}
    where coalesce(minutes, 0) > 0
    group by fixture_sk
)

select
    f.season_sk,
    count(*) as finished_matches_without_player_stats
from {{ ref('fct_fixture') }} as f
inner join served
    on f.season_sk = served.season_sk
left join with_stats
    on f.fixture_sk = with_stats.fixture_sk
where f.status_short in ('FT', 'AET', 'PEN') and with_stats.fixture_sk is null
group by f.season_sk
