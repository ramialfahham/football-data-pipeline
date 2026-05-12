-- Active competitions with current-season fixture statistics coverage must have
-- rows in base_apif__fixture_statistics. Registry/var sync: check_registry_var_sync.py.
{{ config(severity = 'error') }}

with expected_codes as (
    {%- for code in var('active_competition_league_codes') %}
    select '{{ code }}' as league_code
    {%- if not loop.last %}

    union all
    {% endif %}
    {%- endfor %}
),

stats_required as (
    select distinct l.league_code
    from expected_codes as e
    inner join {{ ref('base_apif__leagues') }} as l
        on e.league_code = l.league_code
    where
        l.season_is_current
        and coalesce(l.has_coverage_fixture_statistics, false)
),

present as (
    select distinct league_code from {{ ref('base_apif__fixture_statistics') }}
)

select r.league_code
from stats_required as r
left join present as p on r.league_code = p.league_code
where p.league_code is null
