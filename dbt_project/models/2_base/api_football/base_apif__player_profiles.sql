-- Current per-player BIO from the rich /players/profiles source. stg_apif__player_profiles
-- union-all-accumulates snapshots (skip-if-present loader), so reduce to the latest row per
-- player_id. Identity-level only — no league_code/team/season (those live in the mapping/facts).
-- Feeds dim_player's bio enrichment 1:1. Grain: player_api_id.
--
-- player_birth_country is reconciled here against country_name_overrides (#69), the same
-- seed + left join + coalesce pattern base_apif__leagues.sql and base_apif__teams_global.sql
-- already use — base prepares the correction, dim_player publishes it unchanged.
with src as (
    select * from {{ ref('stg_apif__player_profiles') }}
    where player_id is not null
),

import_country_name_overrides as (
    select * from {{ ref('country_name_overrides') }}
),

renamed as (
    select
        player_name,
        player_firstname as player_first_name,
        player_lastname as player_last_name,
        birth_date as player_birth_date,
        birth_place as player_birth_place,
        birth_country as player_birth_country_raw,
        nationality as player_nationality,
        height as player_height,
        weight as player_weight,
        position as player_position,
        player_photo_url,
        raw_ingested_at,
        safe_cast(player_id as int64) as player_api_id
    from src
),

corrected as (
    select
        renamed.player_name,
        renamed.player_first_name,
        renamed.player_last_name,
        renamed.player_birth_date,
        renamed.player_birth_place,
        renamed.player_nationality,
        renamed.player_height,
        renamed.player_weight,
        renamed.player_position,
        renamed.player_photo_url,
        renamed.raw_ingested_at,
        renamed.player_api_id,
        coalesce(overrides.country_name, renamed.player_birth_country_raw) as player_birth_country
    from renamed
    left join import_country_name_overrides as overrides
        on renamed.player_birth_country_raw = overrides.provider_country
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
from corrected
qualify row_number() over (
    partition by player_api_id
    order by raw_ingested_at desc
) = 1
