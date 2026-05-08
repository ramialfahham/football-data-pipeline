{{ config(materialized='table') }}

with bl1_standings as (
    select * from {{ ref('base_apif__bl1_standings') }}
),

base as (
    {{ union_all(['bl1_standings']) }}
),

season_keys as (
    select
        season_api_year,
        league_code,
        season_sk
    from {{ ref('dim_competition_season') }}
)

select
    {{ dbt_utils.generate_surrogate_key([
        'cs.league_code', 'cs.season', 'cs.team_id', 'cs.group_description'
    ]) }} as standing_sk,
    sk.season_sk,
    cast(cs.team_id as int64) as team_sk,
    cs.league_code,
    cs.season as season_api_year,
    cs.team_id as team_api_id,
    cs.group_description,
    cs.standing_rank,
    cs.points,
    cs.goals_diff,
    cs.form,
    cs.played_all as played,
    cs.wins_all as wins,
    cs.draws_all as draws,
    cs.losses_all as losses,
    cs.raw_ingested_at
from base as cs
inner join season_keys as sk
    on
        cs.league_code = sk.league_code
        and cs.season = sk.season_api_year
