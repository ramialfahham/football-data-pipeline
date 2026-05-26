{{ config(materialized='view') }}

{#
    Top scorers per (league_code, season_api_year), derived from
    mart_player_season. Replaces the /players/topscorers endpoint we no longer
    ingest. Ranking uses DENSE_RANK so ties share a rank and no ranks are
    skipped; the top-N filter is inclusive of ties.
#}

with mart_player_season as (
    select * from {{ ref('mart_player_season') }}
),

scored as (
    select
        player_season_sk,
        player_sk,
        season_sk,
        league_sk,
        league_code,
        season_api_year,
        player_name,
        player_nationality,
        appearances,
        starts,
        minutes,
        goals,
        assists,
        shots_on_target
    from mart_player_season
    where goals > 0
),

ranked as (
    select
        *,
        dense_rank() over (
            partition by league_code, season_api_year
            order by goals desc, assists desc, minutes asc
        ) as scorer_rank
    from scored
)

select *
from ranked
where scorer_rank <= 25
