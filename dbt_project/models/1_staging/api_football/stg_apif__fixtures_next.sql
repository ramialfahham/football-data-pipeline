with src as (
    select *
    from {{ source('api_football', 'raw_apif_fixtures_next') }}
    qualify row_number() over (partition by league_code order by ingested_at desc) = 1
),

exploded as (
    select
        src.league_code,
        src.ingested_at as raw_ingested_at,
        match_json,
        to_json_string(json_query(src.payload, '$.errors')) as api_errors_json,
        safe_cast(json_value(src.payload, '$.results') as int64) as api_reported_result_count,
        to_json_string(json_query(src.payload, '$.parameters')) as request_parameters_json
    from src,
        unnest({{ apif_payload_response_json_strings('src') }}) as match_json
)

select
    league_code,
    raw_ingested_at,
    api_errors_json,
    api_reported_result_count,
    request_parameters_json,
    safe_cast(json_value(match_json, '$.fixture.id') as int64) as fixture_id,
    safe_cast(json_value(match_json, '$.fixture.timestamp') as int64) as fixture_api_unix_seconds,
    date(safe_cast(json_value(match_json, '$.fixture.date') as timestamp)) as fixture_date,
    safe_cast(json_value(match_json, '$.fixture.date') as timestamp) as kickoff_datetime,
    json_value(match_json, '$.fixture.timezone') as kickoff_timezone,
    json_value(match_json, '$.fixture.status.long') as status_long,
    -- UPPERCASED because the provider is inconsistent about it and the code is matched on
    -- EXACTLY. Measured on prod before the change: `Canc` alongside `CANC` (12 rows against 150),
    -- and `Abd` where the API's own code is `ABD` — which is why the accepted_values test on
    -- fct_fixture.status_short has been warning "Got 2 results" in every build. `upper()` yields the
    -- provider's own canonical codes, so this repairs the field rather than re-coding it.
    -- Casing normalisation is raw cleanup — another input to standardize — so it belongs here
    -- and nowhere downstream.
    upper(json_value(match_json, '$.fixture.status.short')) as status_short,
    safe_cast(json_value(match_json, '$.fixture.status.elapsed') as int64) as status_elapsed,
    safe_cast(json_value(match_json, '$.league.season') as int64) as season,
    safe_cast(json_value(match_json, '$.league.id') as int64) as league_api_id,
    json_value(match_json, '$.league.name') as league_name,
    json_value(match_json, '$.league.round') as round_name,
    safe_cast(json_value(match_json, '$.teams.home.id') as int64) as home_team_id,
    json_value(match_json, '$.teams.home.name') as home_team_name,
    safe_cast(json_value(match_json, '$.teams.away.id') as int64) as away_team_id,
    json_value(match_json, '$.teams.away.name') as away_team_name,
    safe_cast(json_value(match_json, '$.goals.home') as int64) as goals_home,
    safe_cast(json_value(match_json, '$.goals.away') as int64) as goals_away,
    json_value(match_json, '$.fixture.venue.id') as venue_id,
    json_value(match_json, '$.fixture.venue.name') as venue_name,
    json_value(match_json, '$.fixture.venue.city') as venue_city
from exploded
