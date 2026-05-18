{{ config(materialized='table') }}

{#
  FIFA World Cup tournament participants for the current warehouse season of league_code WC.
  Grain: (team_sk). season_api_year = max season on fct_fixture for WC (registry current_season).
#}

with wc_tournament_season as (
    select
        league_code,
        max(season_api_year) as season_api_year
    from {{ ref('fct_fixture') }}
    where league_code = 'WC'
    group by league_code
),

fixture_teams as (
    select
        f.home_team_sk as team_sk,
        f.league_code,
        f.season_api_year
    from {{ ref('fct_fixture') }} as f
    inner join wc_tournament_season as wts
        on
            f.league_code = wts.league_code
            and f.season_api_year = wts.season_api_year
    union distinct
    select
        f.away_team_sk as team_sk,
        f.league_code,
        f.season_api_year
    from {{ ref('fct_fixture') }} as f
    inner join wc_tournament_season as wts
        on
            f.league_code = wts.league_code
            and f.season_api_year = wts.season_api_year
)

select
    team_sk,
    league_code,
    season_api_year
from fixture_teams
