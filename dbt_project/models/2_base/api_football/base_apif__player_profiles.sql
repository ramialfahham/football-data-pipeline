-- Current per-player BIO from the rich /players/profiles source. stg_apif__player_profiles
-- union-all-accumulates snapshots (skip-if-present loader), so reduce to the latest row per
-- player_id. Identity-level only — no league_code/team/season (those live in the mapping/facts).
-- Feeds dim_player's bio enrichment 1:1. Grain: player_api_id.
with src as (
    select * from {{ ref('stg_apif__player_profiles') }}
    where player_id is not null
),

renamed as (
    select
        player_name,
        player_firstname as player_first_name,
        player_lastname as player_last_name,
        birth_date as player_birth_date,
        birth_place as player_birth_place,
        birth_country as player_birth_country,
        nationality as player_nationality,
        height as player_height,
        weight as player_weight,
        position as player_position,
        player_photo_url,
        raw_ingested_at,
        safe_cast(player_id as int64) as player_api_id
    from src
)

select
    player_api_id,
    player_name,
    player_first_name,
    player_last_name,
    player_birth_date,
    player_birth_place,
    player_birth_country,
    player_nationality,
    player_height,
    player_weight,
    player_position,
    player_photo_url,
    raw_ingested_at
from renamed
qualify row_number() over (
    partition by player_api_id
    order by raw_ingested_at desc
) = 1
