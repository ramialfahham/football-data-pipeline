{{ config(materialized='table') }}

with import_base_apif__players as (
    select * from {{ ref('base_apif__players') }}
)

select
    cast(player_api_id as int64) as player_sk,
    player_api_id,
    player_name,
    player_first_name,
    player_last_name,
    player_birth_date,
    player_nationality,
    player_photo_url,
    raw_ingested_at
from import_base_apif__players
