{{ config(materialized='table') }}

with base as (
    select * from {{ ref('base_apif__bl1_players') }}
)

select
    {{ dbt_utils.generate_surrogate_key(['league_code', 'player_api_id']) }} as player_sk,
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
from base
