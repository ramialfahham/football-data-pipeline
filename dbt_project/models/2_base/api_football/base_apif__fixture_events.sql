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
),

recovered as (
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
),

-- Fixture participants (home/away team ids), used to evaluate the reattribute_if_cohabiting
-- override condition below. base_apif__fixtures_next grain is one row per fixture_id. Only
-- fixtures whose two participants are BOTH known are kept, so the IN / NOT IN participant checks
-- in the reattribute join never hit the NOT IN (value, NULL) -> UNKNOWN trap (a fixture with a
-- missing participant id is a separate defect; the override conservatively does not fire there).
fixture_participants as (
    select
        fixture_id,
        cast(home_team_id as int64) as home_team_id,
        cast(away_team_id as int64) as away_team_id
    from {{ ref('base_apif__fixtures_next') }}
    where
        home_team_id is not null
        and away_team_id is not null
),

-- Hand-curated corrections for known provider team-id defects, from
-- seeds/fixture_team_id_overrides.csv. `alias` = unconditional duplicate-id replacement (one
-- club under two provider ids); `reattribute_if_cohabiting` = replace only when the correct id is
-- a fixture participant and the wrong id is not (a mis-attribution between two DISTINCT clubs, so
-- a club's own legitimate events are never touched).
overrides as (
    select
        cast(wrong_team_api_id as int64) as wrong_team_api_id,
        cast(correct_team_api_id as int64) as correct_team_api_id,
        mode
    from {{ ref('fixture_team_id_overrides') }}
)

select
    recovered.league_code,
    recovered.fixture_id,
    recovered.event_index,
    recovered.minute_elapsed,
    recovered.minute_extra,
    recovered.team_name,
    recovered.player_id,
    recovered.player_name,
    recovered.assist_player_name,
    recovered.event_type,
    recovered.event_detail,
    recovered.event_comments,
    recovered.raw_ingested_at,
    coalesce(
        alias_override.correct_team_api_id,
        reattribute_override.correct_team_api_id,
        recovered.team_id
    ) as team_id
from recovered
left join overrides as alias_override
    on
        recovered.team_id = alias_override.wrong_team_api_id
        and alias_override.mode = 'alias'
left join fixture_participants
    on recovered.fixture_id = fixture_participants.fixture_id
left join overrides as reattribute_override
    on
        recovered.team_id = reattribute_override.wrong_team_api_id
        and reattribute_override.mode = 'reattribute_if_cohabiting'
        and reattribute_override.correct_team_api_id in (
            fixture_participants.home_team_id, fixture_participants.away_team_id
        )
        and reattribute_override.wrong_team_api_id not in (
            fixture_participants.home_team_id, fixture_participants.away_team_id
        )
