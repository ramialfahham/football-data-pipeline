with src as (
    select *
    from {{ source('api_football', 'raw_d1_apif_fixtures_next') }}
),

exploded as (
    select
        'D1' as league_code,
        src.ingested_datetime as raw_ingested_datetime,
        to_json_string(json_query(src.payload, '$.errors')) as api_errors_json,
        safe_cast(json_value(src.payload, '$.results') as int64) as api_reported_result_count,
        to_json_string(json_query(src.payload, '$.parameters')) as request_parameters_json,
        match_json
    from src,
    unnest({{ apif_payload_response_json_strings('src') }}) as match_json
)

select
    league_code,
    raw_ingested_datetime,
    safe_cast(json_value(match_json, '$.fixture.id') as int64) as fixture_id,
    safe_cast(json_value(match_json, '$.fixture.timestamp') as int64) as fixture_api_unix_seconds,
    date(safe_cast(json_value(match_json, '$.fixture.date') as timestamp)) as fixture_date,
    safe_cast(json_value(match_json, '$.fixture.date') as timestamp) as kickoff_datetime,
    json_value(match_json, '$.fixture.timezone') as kickoff_timezone,
    json_value(match_json, '$.fixture.status.long') as status_long,
    json_value(match_json, '$.fixture.status.short') as status_short,
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
    json_value(match_json, '$.fixture.venue.city') as venue_city,
    api_errors_json,
    api_reported_result_count,
    request_parameters_json,
    match_json as source_json
from exploded
