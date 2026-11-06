{#
  Every club competition edition with a fixture has a row in competition_season_map. Returns each
  edition without one.
#}
{{ config(store_failures = true, severity = 'error') }}

select distinct
    f.league_code,
    f.season_api_year
from {{ ref('fct_fixture') }} as f
inner join {{ ref('competition_registry') }} as reg
    on f.league_code = reg.league_code
inner join {{ ref('competition_types') }} as typ
    on reg.competition_type = typ.competition_type
left join {{ ref('competition_season_map') }} as m
    on f.league_code = m.league_code and f.season_api_year = m.season_api_year
where typ.entity_type = 'club' and m.league_code is null
