with src as (
    select
        league_code,
        fixture_id,
        event_index,
        minute_elapsed,
        minute_extra,
        team_id,
        team_name,
        player_id,
        player_name,
        assist_player_name,
        event_type,
        event_detail,
        event_comments,
        raw_ingested_at
    from {{ ref('stg_apif__fixture_events') }}
    where
        fixture_id is not null
),

deduped as (
    select *
    from src
    qualify row_number() over (
        partition by league_code, fixture_id, event_index
        order by raw_ingested_at desc
    ) = 1
)

select
    league_code,
    fixture_id,
    event_index,
    minute_elapsed,
    minute_extra,
    team_name,
    player_id,
    player_name,
    assist_player_name,
    event_type,
    event_detail,
    event_comments,
    raw_ingested_at,
    -- Recover a null team_id from the same team's other events in the fixture. Some old
    -- API-Football events (mostly Cards) carry team.name but a null team.id, while the same
    -- team has a valid id on its goals/subs; within (fixture, team_name) we backfill the id so
    -- the event stays attributed and fct_fixture_event.team_sk is never null for a named event.
    -- A fixture has two distinct teams with distinct names, so name -> id is unambiguous.
    case
        when team_id is not null then team_id
        when team_name is not null
            then max(team_id) over (
                partition by league_code, fixture_id, team_name
            )
        else team_id
    end as team_id
from deduped
