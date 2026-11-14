-- Coach identity (global entity): one row per coach_api_id from stg_apif__coaches. Each bio field is
-- the newest value any fetch carried; age and photo are the latest fetch's, as age changes with time.
-- Identity only — no league_code (a coach is one entity across the leagues we pull); "which clubs /
-- when" lives in base_apif__coach_career and the mapping. Feeds dim_coach 1:1. Grain: coach_api_id.
--
-- coach_birth_country is reconciled here against country_name_overrides (#69), the same
-- seed + left join + coalesce pattern base_apif__leagues.sql and base_apif__teams_global.sql
-- already use — base prepares the correction, dim_coach publishes it unchanged.
with src as (
    select
        stg.*,
        to_json_string(stg) as row_order
    from {{ ref('stg_apif__coaches') }} as stg
    where stg.coach_id is not null
),

import_country_name_overrides as (
    select * from {{ ref('country_name_overrides') }}
),

{%- set bio = [
    'coach_name', 'coach_first_name', 'coach_last_name', 'coach_birth_date', 'coach_birth_place',
    'coach_birth_country', 'coach_nationality'
] %}

newest as (
    select
        coach_id as coach_api_id,
        {%- for field in bio %}
        array_agg({{ field }} ignore nulls order by raw_ingested_at desc, row_order asc limit 1)[safe_offset(0)]
            as {{ field }},
        {%- endfor %}
        array_agg(
            struct(coach_age, coach_photo_url, raw_ingested_at) order by raw_ingested_at desc, row_order asc limit 1
        )[offset(0)] as latest
    from src
    group by coach_id
),

corrected as (
    select
        newest.coach_api_id,
        newest.coach_name,
        newest.coach_first_name,
        newest.coach_last_name,
        newest.coach_birth_date,
        newest.coach_birth_place,
        newest.coach_nationality,
        newest.latest.coach_age,
        newest.latest.coach_photo_url,
        newest.latest.raw_ingested_at,
        coalesce(overrides.country_name, newest.coach_birth_country) as coach_birth_country
    from newest
    left join import_country_name_overrides as overrides
        on newest.coach_birth_country = overrides.provider_country
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
