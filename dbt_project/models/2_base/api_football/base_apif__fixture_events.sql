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
)

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
from src
qualify row_number() over (
    partition by league_code, fixture_id, event_index
    order by raw_ingested_at desc
) = 1
