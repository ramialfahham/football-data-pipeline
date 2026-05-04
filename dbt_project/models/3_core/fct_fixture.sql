{{ config(materialized='table') }}

with base as (
    select * from {{ ref('base_apif__bl1_fixtures_next') }}
)

select
    cast(fixture_id as int64) as fixture_sk,
    fixture_id as fixture_api_id,
    cast(league_api_id as int64) as league_sk,
    {{ dbt_utils.generate_surrogate_key(['league_api_id', 'season']) }} as season_sk,
    cast(home_team_id as int64) as home_team_sk,
    cast(away_team_id as int64) as away_team_sk,
    cast(format_date('%Y%m%d', fixture_date) as int64) as kickoff_date_sk,
    league_code,
    season as season_api_year,
    home_team_id as home_team_api_id,
    away_team_id as away_team_api_id,
    fixture_date,
    kickoff_datetime,
    kickoff_timezone,
    status_short,
    status_long,
    status_elapsed,
    round_name,
    goals_home,
    goals_away,
    venue_id as venue_api_id,
    venue_name as venue_name_snapshot,
    venue_city as venue_city_snapshot,
    raw_ingested_at
from base
