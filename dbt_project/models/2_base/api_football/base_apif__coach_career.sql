-- Coach<->team career stints, deduped one row per (coach, team, start_date) from
-- stg_apif__coach_career. The authoritative "clubs managed" history. The career team set exceeds
-- dim_team (youth/reserve/untracked clubs), so the team link stays on the provider id. Feeds
-- dim_coach_team_mapping. Grain: (coach_api_id, team_api_id, start_date).
with src as (
    select * from {{ ref('stg_apif__coach_career') }}
    where
        coach_id is not null
        and team_id is not null
        -- start_date is the stint grain key; a stint with no known start is dropped (currently 0 rows)
        -- so the (coach, team, start_date) grain + surrogate key can't collide on null.
        and start_date is not null
)

select
    coach_id as coach_api_id,
    team_id as team_api_id,
    team_name,
    start_date,
    end_date,
    raw_ingested_at
from src
qualify row_number() over (
    partition by coach_id, team_id, start_date
    order by raw_ingested_at desc
) = 1
