{{ config(materialized='table') }}

{#
  Coach<->team AFFILIATION: one row per (coach, team, stint) — the managerial career history (clubs
  managed) with start/end dates, from base_apif__coach_career. team_sk is a SOFT link to dim_team:
  the career team set (youth / reserve / foreign-untracked clubs) exceeds our tracked dim_team, so
  team_sk may not resolve to a dim_team row — the provider team_api_id + team_name are kept for
  display, and no strict relationships test is asserted on team_sk. coach_sk relates to dim_coach.
  Grain: (coach_sk, team_api_id, start_date).
#}

with import_base_apif__coach_career as (
    select * from {{ ref('base_apif__coach_career') }}
)

select
    {{ dbt_utils.generate_surrogate_key(['coach_api_id', 'team_api_id', 'start_date']) }}
        as coach_team_stint_sk,
    cast(coach_api_id as int64) as coach_sk,
    cast(team_api_id as int64) as team_sk,
    coach_api_id,
    team_api_id,
    team_name,
    start_date,
    end_date,
    raw_ingested_at
from import_base_apif__coach_career
