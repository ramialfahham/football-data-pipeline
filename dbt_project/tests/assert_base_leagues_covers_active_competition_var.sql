-- Proves each vars.active_competition_league_codes value exists in base_apif__leagues.
-- Does NOT prove the var matches docs/competition_registry.yml; that is
-- scripts/check_registry_var_sync.py in CI. See dbt_project/dbt_project.yml.
{{ config(severity = 'error') }}

with expected as (
    {%- for code in var('active_competition_league_codes') %}
    select '{{ code }}' as league_code{% if not loop.last %} union all{% endif %}
    {%- endfor %}
),
present as (
    select distinct league_code from {{ ref('base_apif__leagues') }}
)

select e.league_code
from expected as e
left join present as p on e.league_code = p.league_code
where p.league_code is null
