{{ config(materialized='table') }}

{#
  One row per fixture: denormalised teams, league, season, kickoff
  (same shape as mart_fixture_results). Feeds matchday ints and mart_fixture_results.
#}

with import_fct_fixture as (
    select * from {{ ref('fct_fixture') }}
),

import_dim_team as (
    select * from {{ ref('dim_team') }}
),

import_dim_league as (
    select * from {{ ref('dim_league') }}
),

import_dim_competition_season as (
    select * from {{ ref('dim_competition_season') }}
),

import_dim_date as (
    select * from {{ ref('dim_date') }}
)

select
    f.fixture_sk,
    f.fixture_api_id,
    f.league_sk,
    f.season_sk,
    f.home_team_sk,
    f.away_team_sk,
    f.kickoff_date_sk,
    f.league_code,
    f.season_api_year,
    f.fixture_date,
    f.kickoff_datetime,
    f.kickoff_timezone,
    f.status_short,
    f.status_long,
    f.status_elapsed,
    f.round_name,
    f.goals_home,
    f.goals_away,
    f.venue_api_id,
    f.venue_name_snapshot,
    f.venue_city_snapshot,
    home.team_name as home_team_name,
    home.team_code as home_team_code,
    home.team_country as home_team_country,
    home.team_logo_url as home_team_logo_url,
    away.team_name as away_team_name,
    away.team_code as away_team_code,
    away.team_country as away_team_country,
    away.team_logo_url as away_team_logo_url,
    l.league_name,
    l.league_country,
    l.league_logo_url,
    s.season_start_date,
    s.season_end_date,
    s.season_is_current,
    d.date_day as kickoff_date,
    d.day_of_week_name as kickoff_day_of_week,
    d.is_weekend as kickoff_is_weekend,
    f.raw_ingested_at,
    case
        when f.status_short not in ('FT', 'AET', 'PEN') then null
        when f.goals_home > f.goals_away then 'HOME'
        when f.goals_home < f.goals_away then 'AWAY'
        else 'DRAW'
    end as match_outcome
from import_fct_fixture as f
left join import_dim_team as home on f.home_team_sk = home.team_sk
left join import_dim_team as away on f.away_team_sk = away.team_sk
left join import_dim_league as l on f.league_sk = l.league_sk
left join import_dim_competition_season as s on f.season_sk = s.season_sk
left join import_dim_date as d on f.kickoff_date_sk = d.date_sk
