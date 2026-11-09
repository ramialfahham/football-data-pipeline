-- Current per-player BIO from the rich /players/profiles source. stg_apif__player_profiles
-- union-all-accumulates snapshots (skip-if-present loader), so reduce to the latest row per
-- player_id. Identity-level only — no league_code/team/season (those live in the mapping/facts).
-- Feeds dim_player's bio enrichment 1:1. Grain: player_api_id.
--
-- player_birth_country is reconciled here against country_name_overrides (#69), the same
-- seed + left join + coalesce pattern base_apif__leagues.sql and base_apif__teams_global.sql
-- already use — base prepares the correction, dim_player publishes it unchanged.
-- player_nationality goes through the same seed after the bio correction.
with src as (
    select * from {{ ref('stg_apif__player_profiles') }}
    where player_id is not null
),

import_country_name_overrides as (
    select * from {{ ref('country_name_overrides') }}
),

import_player_bio_corrections as (
    select * from {{ ref('player_bio_corrections') }}
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
        {{ player_id_override('safe_cast(player_id as int64)') }} as player_api_id
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
),

latest as (
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
        order by
            player_birth_date is null asc,
            raw_ingested_at desc,
            player_nationality is null asc,
            player_birth_date asc,
            player_nationality asc,
            player_name asc,
            player_first_name asc,
            player_last_name asc,
            player_birth_place asc,
            player_birth_country asc,
            player_height asc,
            player_weight asc,
            player_position asc,
            player_photo_url asc
    ) = 1
),

bio_corrected as (
    select
        latest.player_api_id,
        latest.player_name,
        latest.player_first_name,
        latest.player_last_name,
        latest.player_birth_place,
        latest.player_birth_country,
        latest.player_height,
        latest.player_weight,
        latest.player_position,
        latest.player_photo_url,
        latest.raw_ingested_at,
        safe_cast(
            {{ bio_correction(
                'birth_date_fix',
                'cast(' ~ possible_birth_date('latest.player_birth_date', 'latest.raw_ingested_at') ~ ' as string)'
            ) }} as date
        ) as player_birth_date,
        nullif(
            trim(
                coalesce(
                    nationality_overrides.country_name,
                    {{ bio_correction('nationality_fix', 'latest.player_nationality') }}
                )
            ),
            ''
        ) as player_nationality
    from latest
    left join import_player_bio_corrections as birth_date_fix
        on
            latest.player_api_id = birth_date_fix.player_api_id
            and birth_date_fix.corrected_field = 'player_birth_date'
    left join import_player_bio_corrections as nationality_fix
        on
            latest.player_api_id = nationality_fix.player_api_id
            and nationality_fix.corrected_field = 'player_nationality'
    -- the provider's exact string is the seed's key, garbled spellings included
    left join import_country_name_overrides as nationality_overrides
        on
            {{ bio_correction('nationality_fix', 'latest.player_nationality') }}
            = nationality_overrides.provider_country
)

select
    player_api_id,
    player_birth_date,
    player_birth_place,
    player_birth_country,
    player_height,
    player_weight,
    player_position,
    player_photo_url,
    raw_ingested_at,
    {{ repair_garbled_text('player_name') }} as player_name,
    {{ repair_garbled_text('player_first_name') }} as player_first_name,
    {{ repair_garbled_text('player_last_name') }} as player_last_name,
    {{ repair_garbled_text('player_nationality') }} as player_nationality
from bio_corrected
