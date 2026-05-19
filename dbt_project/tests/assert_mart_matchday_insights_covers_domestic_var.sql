-- When a domestic league has upcoming regular-season fixtures in int_matchday, the unified
-- mart_matchday_insights must include that league_code (BL1 relegation rounds excluded).

{{ config(severity = 'error') }}

with domestic_expected as (
    {%- set first = true -%}
    {%- for code in var('active_competition_league_codes') -%}
        {%- if code != 'WC' and not code.startswith('WCQ') -%}
            {%- if not first %} union all{% endif %}
    select '{{ code }}' as league_code
            {%- set first = false -%}
        {%- endif -%}
    {%- endfor %}
),

upcoming_by_league as (
    select distinct league_code
    from {{ ref('int_matchday__upcoming_round_fixtures') }}
    where
        league_code in (select league_code from domestic_expected)
        and not (
            league_code = 'BL1'
            and round_name in {{ bl1_relegation_round_names_in_clause() }}
        )
),

mart_leagues as (
    select distinct league_code
    from {{ ref('mart_matchday_insights') }}
)

select u.league_code
from upcoming_by_league as u
left join mart_leagues as m on u.league_code = m.league_code
where m.league_code is null
