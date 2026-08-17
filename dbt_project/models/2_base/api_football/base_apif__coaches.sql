-- Coach identity (global entity): one row per coach_api_id from stg_apif__coaches, latest ingest wins.
-- Identity only — no league_code (a coach is one entity across the leagues we pull); "which clubs /
-- when" lives in base_apif__coach_career and the mapping. Feeds dim_coach 1:1. Grain: coach_api_id.
--
-- coach_birth_country is reconciled here against country_name_overrides (#69), the same
-- seed + left join + coalesce pattern base_apif__leagues.sql and base_apif__teams_global.sql
-- already use — base prepares the correction, dim_coach publishes it unchanged.
with src as (
    select * from {{ ref('stg_apif__coaches') }}
    where coach_id is not null
),

import_country_name_overrides as (
    select * from {{ ref('country_name_overrides') }}
),

corrected as (
    select
        src.coach_id as coach_api_id,
        src.coach_name,
        src.coach_first_name,
        src.coach_last_name,
        src.coach_age,
        src.coach_birth_date,
        src.coach_birth_place,
        src.coach_nationality,
        src.coach_photo_url,
        src.raw_ingested_at,
        coalesce(overrides.country_name, src.coach_birth_country) as coach_birth_country
    from src
    left join import_country_name_overrides as overrides
        on src.coach_birth_country = overrides.provider_country
)

select
    coach_api_id,
    coach_name,
    coach_first_name,
    coach_last_name,
    coach_age,
    coach_birth_date,
    coach_birth_place,
    coach_birth_country,
    coach_nationality,
    coach_photo_url,
    raw_ingested_at
from corrected
qualify row_number() over (
    partition by coach_api_id
    order by raw_ingested_at desc
) = 1
