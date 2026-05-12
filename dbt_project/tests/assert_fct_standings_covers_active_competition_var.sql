-- Proves each var league_code has at least one row in fct_standings (after dim join).
-- Registry/var sync: scripts/check_registry_var_sync.py in CI.
{{ config(severity = 'error') }}

with expected as (
    {%- for code in var('active_competition_league_codes') %}
    select '{{ code }}' as league_code{% if not loop.last %} union all{% endif %}
    {%- endfor %}
),
counts as (
    select
        league_code,
        count(*) as n
    from {{ ref('fct_standings') }}
    group by league_code
)

select e.league_code
from expected as e
left join counts as c on e.league_code = c.league_code
where c.n is null or c.n < 1
