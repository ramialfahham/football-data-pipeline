{{ config(materialized='table') }}

with players as (
    select * from {{ ref('base_apif__players') }}
),

profiles as (
    select * from {{ ref('base_apif__player_profiles') }}
)

select
    -- simple passthroughs first (sqlfluff ST06: simple targets before calculations)
    players.player_api_id,
    profiles.player_birth_place,
    profiles.player_birth_country,
    profiles.player_height,
    profiles.player_weight,
    profiles.player_position,
    players.raw_ingested_at,
    -- surrogate key + profile-wins descriptors (/players/profiles is the richer bio source;
    -- fall back to the identity source where absent)
    cast(players.player_api_id as int64) as player_sk,
    coalesce(profiles.player_name, players.player_name) as player_name,
    coalesce(profiles.player_first_name, players.player_first_name) as player_first_name,
    coalesce(profiles.player_last_name, players.player_last_name) as player_last_name,
    coalesce(profiles.player_birth_date, players.player_birth_date) as player_birth_date,
    coalesce(profiles.player_nationality, players.player_nationality) as player_nationality,
    coalesce(profiles.player_photo_url, players.player_photo_url) as player_photo_url
from players
left join profiles
    on players.player_api_id = profiles.player_api_id
