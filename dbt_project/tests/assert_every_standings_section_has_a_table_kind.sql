-- A standings section's table_kind is the lowest-priority seed pattern that matches its name,
-- and a name no pattern matches is the competition's own league table. Two things can go wrong
-- silently: a new section name the seed does not cover falls through to "league" and gets
-- rendered as the competition's ladder next to its real groups; or a seed edit lets one name
-- match two kinds. Both show up as a league-kind section sharing a competition-season with a
-- group or conference section, or as a section resolving to more than one kind.
--
-- Recomputed from fct_standings and the seed, not from the mart's own CTE, so a rewrite of the
-- mart that drops or reorders the resolution fails here.
--
-- Returns a row (= fails) per offending (league_code, season_api_year, group_name).
{{ config(store_failures = true) }}

with sections as (
    select distinct
        league_code,
        season_api_year,
        group_name
    from {{ ref('fct_standings') }}
),

matched as (
    select
        s.league_code,
        s.season_api_year,
        s.group_name,
        k.table_kind,
        k.priority
    from sections as s
    cross join {{ ref('standings_table_kinds') }} as k
    where regexp_contains(lower(s.group_name), k.pattern)
),

first_match as (
    select
        league_code,
        season_api_year,
        group_name,
        table_kind
    from matched
    qualify row_number() over (
        partition by league_code, season_api_year, group_name
        order by priority
    ) = 1
),

resolved as (
    select
        s.league_code,
        s.season_api_year,
        s.group_name,
        coalesce(m.table_kind, 'league') as expected_kind
    from sections as s
    left join first_match as m
        on
            s.league_code = m.league_code
            and s.season_api_year = m.season_api_year
            and s.group_name = m.group_name
),

served as (
    select distinct
        league_code,
        season_api_year,
        group_name,
        table_kind
    from {{ ref('mart_standings') }}
),

season_kinds as (
    select
        league_code,
        season_api_year,
        countif(expected_kind = 'league') as league_sections,
        countif(expected_kind in ('group', 'conference')) as grouped_sections
    from resolved
    group by 1, 2
)

select
    r.league_code,
    r.season_api_year,
    r.group_name,
    r.expected_kind,
    v.table_kind as served_kind
from resolved as r
left join served as v
    on
        r.league_code = v.league_code
        and r.season_api_year = v.season_api_year
        and r.group_name = v.group_name
inner join season_kinds as sk
    on
        r.league_code = sk.league_code
        and r.season_api_year = sk.season_api_year
where
    v.table_kind is null
    or v.table_kind != r.expected_kind
    or (r.expected_kind = 'league' and sk.grouped_sections > 0)
