{{ config(materialized='table') }}

with import_base_apif__players_global as (
    select * from {{ ref('base_apif__players_global') }}
)

select
    cast(player_api_id as int64) as player_sk,
    league_code,
    player_api_id,
    player_name,
    player_first_name,
    player_last_name,
    player_birth_date,
    player_nationality,
    player_photo_url,
    last_known_team_api_id,
    last_known_season_year,
    raw_ingested_at
from import_base_apif__players_global
