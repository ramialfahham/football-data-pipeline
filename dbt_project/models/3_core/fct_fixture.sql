{{ config(materialized='table') }}

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
        raw_ingested_at,
        row_number() over (
            partition by fixture_id
            order by raw_ingested_at desc
        ) as rn
    from {{ ref('stg_apif__d1_fixtures_next') }}
    where fixture_id is not null
)

select
    cast(fixture_id as int64) as fixture_sk,
    fixture_id as fixture_api_id,
    {{ dbt_utils.generate_surrogate_key(['league_code', 'league_api_id']) }} as league_sk,
    {{ dbt_utils.generate_surrogate_key(['league_code', 'season']) }} as season_sk,
    {{ dbt_utils.generate_surrogate_key(['league_code', 'home_team_id']) }} as home_team_sk,
    {{ dbt_utils.generate_surrogate_key(['league_code', 'away_team_id']) }} as away_team_sk,
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
    venue_api_id,
    venue_name as venue_name_snapshot,
    venue_city as venue_city_snapshot,
    raw_ingested_at
from src
where rn = 1
