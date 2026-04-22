{{ config(materialized='view') }}

{#
    Current-season ranking snapshot for consumer apps.
    One row per team in the latest available season for each league.
#}

with mart_team_season as (
    select * from {{ ref('mart_team_season') }}
),

latest_season_per_league as (
    select
        league_code,
        max(season_api_year) as latest_season_api_year
    from mart_team_season
    group by league_code
),

current_rows as (
    select
        mts.team_season_sk,
        mts.team_sk,
        mts.season_sk,
        mts.league_sk,
        mts.league_code,
        mts.season_api_year,
        mts.team_name,
        mts.team_code,
        mts.team_country,
        mts.played,
        mts.wins,
        mts.draws,
        mts.losses,
        mts.goal_diff,
        mts.points
    from mart_team_season as mts
    inner join latest_season_per_league as ls
        on
            mts.league_code = ls.league_code
            and mts.season_api_year = ls.latest_season_api_year
),

ranked as (
    select
        *,
        dense_rank() over (
            partition by league_code
            order by points desc, goal_diff desc, wins desc, team_name asc
        ) as current_rank
    from current_rows
)

select * from ranked
