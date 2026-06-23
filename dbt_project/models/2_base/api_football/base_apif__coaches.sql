-- Coach identity (global entity): one row per coach_api_id from stg_apif__coaches, latest ingest wins.
-- Identity only — no league_code (a coach is one entity across the leagues we pull); "which clubs /
-- when" lives in base_apif__coach_career and the mapping. Feeds dim_coach 1:1. Grain: coach_api_id.
with src as (
    select * from {{ ref('stg_apif__coaches') }}
    where coach_id is not null
)

select
    coach_id as coach_api_id,
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
from src
qualify row_number() over (
    partition by coach_id
    order by raw_ingested_at desc
) = 1
