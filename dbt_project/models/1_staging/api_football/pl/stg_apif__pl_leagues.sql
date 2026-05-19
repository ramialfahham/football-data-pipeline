with src as (
    select *
    from {{ source('api_football', 'raw_apif_pl_leagues') }}
),

league_rows as (
    select
        'PL' as league_code,
        src.ingested_at as raw_ingested_at,
        row_json,
        to_json_string(json_query(src.payload, '$.errors')) as api_errors_json,
        safe_cast(json_value(src.payload, '$.results') as int64) as api_reported_result_count,
        to_json_string(json_query(src.payload, '$.parameters')) as request_parameters_json
    from src,
        unnest({{ apif_payload_response_json_strings('src') }}) as row_json
),

season_rows_raw as (
    select
        league_code,
        raw_ingested_at,
        api_errors_json,
        api_reported_result_count,
        request_parameters_json,
        row_json,
        season_el
    from league_rows,
        unnest(
            coalesce(
                json_query_array(
                    json_query(safe.parse_json(row_json), '$.seasons'),
                    '$'
                ),
                []
            )
        ) as season_el
    where json_value(season_el, '$.year') is not null
),

season_rows as (
    select
        league_code,
        raw_ingested_at,
        api_errors_json,
        api_reported_result_count,
        request_parameters_json,
        row_json,
        season_el,
        safe_cast(json_value(row_json, '$.league.id') as int64) as league_api_id,
        json_value(row_json, '$.league.name') as league_name,
        json_value(row_json, '$.league.type') as league_type,
        json_value(row_json, '$.league.country') as country,
        json_value(row_json, '$.league.logo') as league_logo_url,
        json_value(row_json, '$.league.flag') as country_flag_url
    from season_rows_raw
)

select
    league_code,
    raw_ingested_at,
    api_errors_json,
    api_reported_result_count,
    request_parameters_json,
    row_json as source_json,
    league_api_id,
    league_name,
    league_type,
    country,
    league_logo_url,
    country_flag_url,
    safe_cast(json_value(season_el, '$.year') as int64) as season_api_year,
    safe_cast(json_value(season_el, '$.start') as date) as season_start_date,
    safe_cast(json_value(season_el, '$.end') as date) as season_end_date,
    safe_cast(json_value(season_el, '$.current') as bool) as season_is_current,
    safe_cast(json_value(season_el, '$.coverage.fixtures.events') as bool)
        as has_coverage_fixture_events,
    safe_cast(json_value(season_el, '$.coverage.fixtures.lineups') as bool)
        as has_coverage_fixture_lineups,
    safe_cast(json_value(season_el, '$.coverage.fixtures.statistics_fixtures') as bool)
        as has_coverage_fixture_statistics,
    safe_cast(json_value(season_el, '$.coverage.fixtures.statistics_players') as bool)
        as has_coverage_fixture_players,
    safe_cast(json_value(season_el, '$.coverage.standings') as bool) as has_coverage_standings,
    safe_cast(json_value(season_el, '$.coverage.players') as bool) as has_coverage_players,
    safe_cast(json_value(season_el, '$.coverage.top_scorers') as bool) as has_coverage_top_scorers,
    safe_cast(json_value(season_el, '$.coverage.top_assists') as bool) as has_coverage_top_assists,
    safe_cast(json_value(season_el, '$.coverage.top_cards') as bool) as has_coverage_top_cards,
    safe_cast(json_value(season_el, '$.coverage.injuries') as bool) as has_coverage_injuries,
    safe_cast(json_value(season_el, '$.coverage.predictions') as bool) as has_coverage_predictions,
    safe_cast(json_value(season_el, '$.coverage.odds') as bool) as has_coverage_odds
from season_rows
