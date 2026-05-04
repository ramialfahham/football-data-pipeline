with src as (
    select *
    from {{ source('api_football', 'raw_apif_wc_qualifier_fixtures') }}
),

league_blocks as (
    select
        src.ingested_at as raw_ingested_at,
        block_json,
        safe_cast(json_value(block_json, '$.queried_league_id') as int64) as queried_league_id
    from src,
        unnest(coalesce(json_query_array(src.payload, '$.response'), [])) as block_json
),

fixtures as (
    select
        raw_ingested_at,
        queried_league_id,
        fixture_el
    from league_blocks,
        unnest(
            coalesce(json_query_array(block_json, '$.response'), [])
        ) as fixture_el
)

select
    -- queried_league_id maps to the confederation qualifier league_code.
    -- Mapping is stable for WC 2026; update here when supporting_leagues changes in the registry.
    case queried_league_id
        when 29 then 'WCQAF'
        when 30 then 'WCQAS'
        when 31 then 'WCQCA'
        when 32 then 'WCQEU'
        when 33 then 'WCQOC'
        when 34 then 'WCQSA'
        when 37 then 'WCQIP'
        else concat('WCQUNK', cast(queried_league_id as string))
    end as league_code,
    safe_cast(json_value(fixture_el, '$.fixture.id') as int64) as fixture_id,
    date(safe_cast(json_value(fixture_el, '$.fixture.date') as timestamp)) as fixture_date,
    safe_cast(json_value(fixture_el, '$.fixture.date') as timestamp) as kickoff_datetime,
    json_value(fixture_el, '$.fixture.timezone') as kickoff_timezone,
    json_value(fixture_el, '$.fixture.status.short') as status_short,
    json_value(fixture_el, '$.fixture.status.long') as status_long,
    safe_cast(json_value(fixture_el, '$.fixture.status.elapsed') as int64) as status_elapsed,
    safe_cast(json_value(fixture_el, '$.league.id') as int64) as league_api_id,
    safe_cast(json_value(fixture_el, '$.league.season') as int64) as season,
    json_value(fixture_el, '$.league.round') as round_name,
    safe_cast(json_value(fixture_el, '$.teams.home.id') as int64) as home_team_id,
    safe_cast(json_value(fixture_el, '$.teams.away.id') as int64) as away_team_id,
    safe_cast(json_value(fixture_el, '$.goals.home') as int64) as goals_home,
    safe_cast(json_value(fixture_el, '$.goals.away') as int64) as goals_away,
    json_value(fixture_el, '$.fixture.venue.id') as venue_id,
    json_value(fixture_el, '$.fixture.venue.name') as venue_name,
    json_value(fixture_el, '$.fixture.venue.city') as venue_city,
    to_json_string(fixture_el) as source_json,
    raw_ingested_at
from fixtures
where safe_cast(json_value(fixture_el, '$.fixture.id') as int64) is not null
