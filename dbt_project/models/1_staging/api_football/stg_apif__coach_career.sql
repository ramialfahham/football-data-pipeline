-- Coach managerial history: one row per (coach, career stint) — flattened from RAW_APIF_COACHES
-- payload.response[].coach.career[] (team + start/end). RAW_APIF_COACHES is a complete snapshot per
-- (league_code, run); staging reads ALL snapshots faithfully (NOT latest-per-league) — CPO-ruled this
-- session to preserve every coach's history (see stg_apif__coaches / escalations.log). base dedups the
-- stints. The career team set is broader than dim_team (youth/reserve/untracked clubs), so team_id is
-- kept as the provider id. See dbt_project/docs/layering.md §1_staging.
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
    coaches.league_code,
    coaches.raw_ingested_at,
    safe_cast(json_value(coaches.coach_el, '$.coach.id') as int64) as coach_id,
    safe_cast(json_value(career_el, '$.team.id') as int64) as team_id,
    json_value(career_el, '$.team.name') as team_name,
    safe_cast(json_value(career_el, '$.start') as date) as start_date,
    safe_cast(json_value(career_el, '$.end') as date) as end_date
from coaches,
    unnest(json_query_array(coaches.coach_el, '$.coach.career')) as career_el
