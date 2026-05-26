with src as (
    select *
    from {{ source('api_football', 'raw_apif_wcqoc_fixture_details') }}
),

fixtures as (
    select
        src.ingested_at as raw_ingested_at,
        src.payload as fixture_json,
        'WCQOC' as league_code
    from src
),

events as (
    select
        league_code,
        raw_ingested_at,
        event_el,
        event_index,
        safe_cast(json_value(fixture_json, '$.fixture.id') as int64) as fixture_id
    from fixtures,
        unnest(json_query_array(fixture_json, '$.events')) as event_el with offset as event_index
)

select
    league_code,
    raw_ingested_at,
    fixture_id,
    event_index,
    safe_cast(json_value(event_el, '$.time.elapsed') as int64) as minute_elapsed,
    safe_cast(json_value(event_el, '$.time.extra') as int64) as minute_extra,
    safe_cast(json_value(event_el, '$.team.id') as int64) as team_id,
    json_value(event_el, '$.team.name') as team_name,
    json_value(event_el, '$.player.name') as player_name,
    safe_cast(json_value(event_el, '$.player.id') as int64) as player_id,
    json_value(event_el, '$.assist.name') as assist_player_name,
    json_value(event_el, '$.type') as event_type,
    json_value(event_el, '$.detail') as event_detail,
    json_value(event_el, '$.comments') as event_comments,
    to_json_string(event_el) as source_json
from events
