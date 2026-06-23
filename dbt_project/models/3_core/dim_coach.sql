{{ config(materialized='table') }}

{#
  Pure coach ENTITY: one row per coach_api_id (identity / bio only; NO league_code — mirrors
  dim_player and dim_team). "Which clubs and when" lives in dim_coach_team_mapping, not here.
  Grain: coach_sk.
#}

with import_base_apif__coaches as (
    select * from {{ ref('base_apif__coaches') }}
)

select
    cast(coach_api_id as int64) as coach_sk,
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
from import_base_apif__coaches
