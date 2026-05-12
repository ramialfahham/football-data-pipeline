{{ config(materialized='table') }}

with import_base_apif__competition_seasons as (
    select * from {{ ref('base_apif__competition_seasons') }}
)

select
    {{ dbt_utils.generate_surrogate_key(['league_api_id', 'season_api_year']) }} as season_sk,
    cast(league_api_id as int64) as league_sk,
    league_code,
    league_api_id,
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
from import_base_apif__competition_seasons
