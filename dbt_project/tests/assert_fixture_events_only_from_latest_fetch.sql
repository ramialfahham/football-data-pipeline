{#
  A match's events are those of its latest fetch that has events. Returns one row per event in
  base_apif__fixture_events or fct_fixture_event at a position that fetch does not have.
#}
{{ config(store_failures = true, severity = 'error') }}

with fetches as (
    select
        league_code,
        fixture_id,
        raw_ingested_at,
        max(event_index) + 1 as event_count
    from {{ ref('stg_apif__fixture_events') }}
    where fixture_id is not null
    group by league_code, fixture_id, raw_ingested_at
),

latest_fetch as (
    select
        league_code,
        fixture_id,
        array_agg(event_count order by raw_ingested_at desc limit 1)[offset(0)] as event_count
    from fetches
    group by league_code, fixture_id
),

held as (
    select
        'base_apif__fixture_events' as model_name,
        league_code,
        fixture_id,
        event_index
    from {{ ref('base_apif__fixture_events') }}
    union all
    select
        'fct_fixture_event' as model_name,
        league_code,
        fixture_api_id as fixture_id,
        event_index
    from {{ ref('fct_fixture_event') }}
)

select
    held.model_name,
    held.league_code,
    held.fixture_id,
    held.event_index,
    latest_fetch.event_count as latest_fetch_event_count
from held
inner join latest_fetch
    on
        held.league_code = latest_fetch.league_code
        and held.fixture_id = latest_fetch.fixture_id
where held.event_index >= latest_fetch.event_count
