{{ config(materialized='table') }}

{#
    One row per transfer event per player. A player can have many transfers;
    transfers_json is an array on the player staging row.

    Transfers frequently involve teams outside D1 (e.g. incoming from a foreign
    league), which will not resolve to dim_team. from_team_sk / to_team_sk are
    therefore nullable by design; from_team_api_id / from_team_name_snapshot
    always come through so the fact stays self-sufficient.
#}

with src as (
    select * from {{ ref('base_apif__bl1_transfers') }}
)

select
    {{ dbt_utils.generate_surrogate_key([
        'league_code',
        'player_id',
        'transfer_date',
        'from_team_api_id',
        'to_team_api_id',
        'transfer_type'
    ]) }} as transfer_sk,
    {{ dbt_utils.generate_surrogate_key(['league_code', 'player_id']) }} as player_sk,
    case
        when from_team_api_id is not null
            then {{ dbt_utils.generate_surrogate_key(['league_code', 'from_team_api_id']) }}
    end as from_team_sk,
    case
        when to_team_api_id is not null
            then {{ dbt_utils.generate_surrogate_key(['league_code', 'to_team_api_id']) }}
    end as to_team_sk,
    cast(format_date('%Y%m%d', transfer_date) as int64) as transfer_date_sk,
    league_code,
    player_id as player_api_id,
    transfer_date,
    transfer_type,
    from_team_api_id,
    from_team_name_snapshot,
    to_team_api_id,
    to_team_name_snapshot,
    raw_ingested_at
from src
