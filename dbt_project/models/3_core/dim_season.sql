{{ config(materialized='table') }}

with leagues_src as (
    select
        league_code,
        league_api_id,
        raw_ingested_at,
        seasons_json
    from {{ ref('stg_apif__d1_leagues') }}
    where seasons_json is not null
),

exploded as (
    select
        league_code,
        league_api_id,
        raw_ingested_at,
        season_el
    from leagues_src,
        unnest(json_query_array(seasons_json, '$')) as season_el
),

parsed as (
    select
        league_code,
        league_api_id,
        raw_ingested_at,
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
    from exploded
),

ranked as (
    select
        *,
        row_number() over (
            partition by league_code, season_api_year
            order by raw_ingested_at desc
        ) as rn
    from parsed
    where season_api_year is not null
)

select
    {{ dbt_utils.generate_surrogate_key(['league_code', 'season_api_year']) }} as season_sk,
    {{ dbt_utils.generate_surrogate_key(['league_code', 'league_api_id']) }} as league_sk,
    league_code,
    season_api_year,
    season_start_date,
    season_end_date,
    season_is_current,
    has_coverage_fixture_events,
    has_coverage_fixture_lineups,
    has_coverage_fixture_statistics,
    has_coverage_fixture_players,
    has_coverage_standings,
    has_coverage_players,
    has_coverage_top_scorers,
    has_coverage_top_assists,
    has_coverage_top_cards,
    has_coverage_injuries,
    has_coverage_predictions,
    has_coverage_odds,
    raw_ingested_at
from ranked
where rn = 1
