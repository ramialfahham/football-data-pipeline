{{ config(materialized='table') }}

with current_snapshot as (
    select
        season,
        team_id,
        group_description,
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
        replace(league_code, 'D1', 'BL1') as league_code
    from {{ ref('snap_apif_d1_standings') }}
    where dbt_valid_to is null
)

select
    {{ dbt_utils.generate_surrogate_key([
        'league_code', 'season', 'team_id', 'group_description'
    ]) }} as standing_sk,
    {{ dbt_utils.generate_surrogate_key(['league_code', 'season']) }} as season_sk,
    {{ dbt_utils.generate_surrogate_key(['league_code', 'team_id']) }} as team_sk,
    league_code,
    season as season_api_year,
    team_id as team_api_id,
    group_description,
    standing_rank,
    points,
    goals_diff,
    form,
    played,
    wins,
    draws,
    losses,
    raw_ingested_at,
    snapshot_valid_from
from current_snapshot
