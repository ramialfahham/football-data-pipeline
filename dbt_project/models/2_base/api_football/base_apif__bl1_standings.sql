-- Deduplicated standings rows from stg_apif__bl1_standings. The API returns
-- one row per (league_api_id, season, team_id) representing the team's
-- current league position; ingestion's merge_standings_envelope replaces
-- the whole season block on each refresh, so the raw payload always
-- reflects the latest API state. This base model defensively keeps the
-- most recently ingested version per (league_code, season, team_id).
-- group_description is propagated as the team's current standings zone.
-- Output grain: (league_code, season, team_id).

with src as (
    select
        league_code,
        league_api_id,
        league_name,
        season,
        team_id,
        team_name,
        standing_rank,
        points,
        goals_diff,
        form,
        group_description,
        played_all,
        wins_all,
        draws_all,
        losses_all,
        raw_ingested_at
    from {{ ref('stg_apif__bl1_standings') }}
    where
        team_id is not null
        and season is not null
)

select
    league_code,
    league_api_id,
    league_name,
    season,
    team_id,
    team_name,
    standing_rank,
    points,
    goals_diff,
    form,
    group_description,
    played_all,
    wins_all,
    draws_all,
    losses_all,
    raw_ingested_at
from src
qualify row_number() over (
    partition by league_code, season, team_id
    order by raw_ingested_at desc
) = 1
