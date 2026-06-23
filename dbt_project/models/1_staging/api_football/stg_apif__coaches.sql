-- RAW_APIF_COACHES is a complete snapshot per (league_code, run): one row per league per ingest,
-- whose payload.response[] holds that league's coaches (each as response[].coach — id, name, bio,
-- and a career[] history). Staging reads ALL snapshots faithfully (NOT latest-per-league) — CPO-ruled
-- this session to PRESERVE every coach ever seen (mirrors dim_player/dim_team entity preservation);
-- latest-per-league would drop ~120 coaches whose teams later left our pull. base dedups a coach to
-- one entity (latest ingest). The career[] history is a separate grain (stg_apif__coach_career).
-- See dbt_project/docs/layering.md §1_staging and .claude/task/escalations.log (2026-06-23).
with src as (
    select
        league_code,
        payload,
        ingested_at
    from {{ source('api_football', 'raw_apif_coaches') }}
),

coaches as (
    select
        src.league_code,
        src.ingested_at as raw_ingested_at,
        coach_el
    from src,
        unnest(json_query_array(src.payload, '$.response')) as coach_el
)

select
    league_code,
    raw_ingested_at,
    safe_cast(json_value(coach_el, '$.coach.id') as int64) as coach_id,
    json_value(coach_el, '$.coach.name') as coach_name,
    json_value(coach_el, '$.coach.firstname') as coach_first_name,
    json_value(coach_el, '$.coach.lastname') as coach_last_name,
    safe_cast(json_value(coach_el, '$.coach.age') as int64) as coach_age,
    safe_cast(json_value(coach_el, '$.coach.birth.date') as date) as coach_birth_date,
    json_value(coach_el, '$.coach.birth.place') as coach_birth_place,
    json_value(coach_el, '$.coach.birth.country') as coach_birth_country,
    json_value(coach_el, '$.coach.nationality') as coach_nationality,
    json_value(coach_el, '$.coach.photo') as coach_photo_url
from coaches
