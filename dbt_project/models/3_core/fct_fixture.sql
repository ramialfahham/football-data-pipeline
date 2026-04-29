{{ config(materialized='table') }}

with src as (
    select
        league_code,
        fixture_api_id,
        league_api_id,
        season_api_year,
        fixture_date,
        kickoff_datetime,
        kickoff_timezone,
        status_short,
        status_long,
        status_elapsed,
        round_name,
        home_team_api_id,
        away_team_api_id,
        goals_home,
        goals_away,
        venue_api_id,
        venue_name_snapshot,
        venue_city_snapshot,
        raw_ingested_at
    from {{ ref('base_football__fixtures') }}
    where league_code = 'D1'
)

select
    cast(fixture_api_id as int64) as fixture_sk,
    fixture_api_id,
    {{ dbt_utils.generate_surrogate_key(['league_code', 'league_api_id']) }} as league_sk,
    {{ dbt_utils.generate_surrogate_key(['league_code', 'season_api_year']) }} as season_sk,
    {{ dbt_utils.generate_surrogate_key(['league_code', 'home_team_api_id']) }} as home_team_sk,
    {{ dbt_utils.generate_surrogate_key(['league_code', 'away_team_api_id']) }} as away_team_sk,
    cast(format_date('%Y%m%d', fixture_date) as int64) as kickoff_date_sk,
    league_code,
    season_api_year,
    home_team_api_id,
    away_team_api_id,
    fixture_date,
    kickoff_datetime,
    kickoff_timezone,
    status_short,
    status_long,
    status_elapsed,
    round_name,
    goals_home,
    goals_away,
    venue_api_id,
    venue_name_snapshot,
    venue_city_snapshot,
    raw_ingested_at
from src
