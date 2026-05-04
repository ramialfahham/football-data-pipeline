{{ config(materialized='table') }}

with base as (
    select * from {{ ref('base_apif__bl1_players') }}
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
from base
qualify row_number() over (
    partition by player_api_id
    order by raw_ingested_at desc
) = 1
