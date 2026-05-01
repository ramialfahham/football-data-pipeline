{{ config(materialized='view') }}

with src as (
    select
        league_code,
        fixture_id,
        league_api_id,
        season,
        fixture_date,
        kickoff_datetime,
        kickoff_timezone,
        status_short,
        status_long,
        status_elapsed,
        round_name,
        home_team_id,
        away_team_id,
        goals_home,
        goals_away,
        venue_id as venue_api_id,
        venue_name,
        venue_city,
        raw_ingested_at
    from {{ ref('stg_apif__fixtures_next') }}
    where fixture_id is not null
    qualify row_number() over (
        partition by league_code, fixture_id
        order by raw_ingested_at desc
    ) = 1
)

select
    league_code,
    fixture_id as fixture_api_id,
    league_api_id,
    season as season_api_year,
    fixture_date,
    kickoff_datetime,
    kickoff_timezone,
    status_short,
    status_long,
    status_elapsed,
    round_name,
    home_team_id as home_team_api_id,
    away_team_id as away_team_api_id,
    goals_home,
    goals_away,
    venue_api_id,
    venue_name as venue_name_snapshot,
    venue_city as venue_city_snapshot,
    raw_ingested_at
from src
