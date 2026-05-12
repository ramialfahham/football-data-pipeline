-- Same coverage rule as assert_base_fixture_statistics_covers_active_competition_var for fct.
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

counts as (
    select
        league_code,
        count(*) as n
    from {{ ref('fct_fixture_team_stats') }}
    group by league_code
)

select r.league_code
from stats_required as r
left join counts as c on r.league_code = c.league_code
where c.n is null or c.n < 1
