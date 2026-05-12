-- Proves each active competition that reports /standings coverage has rows in
-- base_apif__standings. Codes in vars.active_competition_league_codes but with
-- has_coverage_standings false (e.g. WCQIP, WCQOC) are excluded — the API has no
-- standings surface for them. Registry/var sync: scripts/check_registry_var_sync.py.
{{ config(severity = 'error') }}

with expected_codes as (
    {%- for code in var('active_competition_league_codes') %}
    select '{{ code }}' as league_code
    {%- if not loop.last %}

    union all
    {% endif %}
    {%- endfor %}
),

standings_required as (
    select distinct l.league_code
    from expected_codes as e
    inner join {{ ref('base_apif__leagues') }} as l
        on e.league_code = l.league_code
    where
        l.season_is_current
        and coalesce(l.has_coverage_standings, false)
),

present as (
    select distinct league_code from {{ ref('base_apif__standings') }}
)

select r.league_code
from standings_required as r
left join present as p on r.league_code = p.league_code
where p.league_code is null
