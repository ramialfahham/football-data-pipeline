{{ config(materialized='table') }}

with current_snapshot as (
    select
        season,
        team_id,
        standing_rank,
        points,
        goals_diff,
        form,
        played_all as played,
        wins_all as wins,
        draws_all as draws,
        losses_all as losses,
        raw_ingested_at,
        dbt_valid_from as snapshot_valid_from,
        league_code,
        group_description
    from {{ ref('snap_apif_d1_standings') }}
    where dbt_valid_to is null
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
    cs.played,
    cs.wins,
    cs.draws,
    cs.losses,
    cs.raw_ingested_at,
    cs.snapshot_valid_from
from current_snapshot as cs
inner join season_keys as sk
    on
        cs.league_code = sk.league_code
        and cs.season = sk.season_api_year
