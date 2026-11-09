{#
  Every club competition edition with a fixture has a row in competition_season_map. Returns each
  edition without one.
#}
{{ config(store_failures = true, severity = 'error') }}

select distinct
    f.league_code,
    f.season_api_year
from {{ ref('fct_fixture') }} as f
inner join {{ ref('dim_league') }} as leagues
    on f.league_code = leagues.league_code
left join {{ ref('competition_season_map') }} as m
    on f.league_code = m.league_code and f.season_api_year = m.season_api_year
where leagues.entity_type = 'club' and m.league_code is null
