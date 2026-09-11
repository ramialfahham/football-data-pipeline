-- RAW_APIF_FIXTURE_DETAILS is APPEND-ONLY and holds one row per FETCH of a fixture: the loader
-- skip-fetches only finished fixtures missing data, and a retry appends a second version rather
-- than replacing the first (ingestion/api_football/loads/batch_fixtures.py: raw keeps both
-- versions). So it carries many fixtures per league_code AND several versions per
-- fixture. Staging reads ALL rows faithfully (NO latest-snapshot qualify — that would drop
-- fixtures) and base assembles current-per-entity by entity-key dedup on raw_ingested_at desc,
-- which is where the choice between versions belongs. See dbt_project/docs/layering.md §1_staging.
with src as (
    select *
    from {{ source('api_football', 'raw_apif_fixture_details') }}
),

events as (
    select
        src.league_code,
        src.ingested_at as raw_ingested_at,
        event_el,
        event_index,
        safe_cast(json_value(src.payload, '$.fixture.id') as int64) as fixture_id
    from src,
        unnest(json_query_array(src.payload, '$.events')) as event_el with offset as event_index
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
    json_value(event_el, '$.comments') as event_comments
from events
