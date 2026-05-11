-- Proves each vars.active_competition_league_codes value exists in base_apif__fixtures_next.
-- Registry/var sync: scripts/check_registry_var_sync.py in CI.
{{ config(severity = 'error') }}

with expected as (
    {%- for code in var('active_competition_league_codes') %}
    select '{{ code }}' as league_code{% if not loop.last %} union all{% endif %}
    {%- endfor %}
),
present as (
    select distinct league_code from {{ ref('base_apif__fixtures_next') }}
)

select e.league_code
from expected as e
left join present as p on e.league_code = p.league_code
where p.league_code is null
