-- A standings section's table_kind is the lowest-priority seed pattern that matches its name,
-- and a name no pattern matches is the competition's own league table. A section holding one team
-- from each of the league-season's other tables is a ranking whatever its name, and so is a section
-- left as a league whose every team also sits in a group or conference section. Two things can go wrong
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

named as (
    select
        s.league_code,
        s.season_api_year,
        s.group_name,
        coalesce(m.table_kind, 'league') as named_kind
    from sections as s
    left join first_match as m
        on
            s.league_code = m.league_code
            and s.season_api_year = m.season_api_year
            and s.group_name = m.group_name
),

team_sections as (
    select distinct
        f.league_code,
        f.season_api_year,
        f.group_name,
        f.team_sk,
        n.named_kind
    from {{ ref('fct_standings') }} as f
    inner join named as n
        on
            f.league_code = n.league_code
            and f.season_api_year = n.season_api_year
            and f.group_name = n.group_name
),

grouped as (
    select distinct
        league_code,
        season_api_year,
        team_sk
    from team_sections
    where named_kind in ('group', 'conference')
),

-- A league-named section none of whose teams is missing from the league-season's group and
-- conference sections combines them.
combined as (
    select
        a.league_code,
        a.season_api_year,
        a.group_name
    from team_sections as a
    left join grouped as g
        on
            a.league_code = g.league_code
            and a.season_api_year = g.season_api_year
            and a.team_sk = g.team_sk
    where a.named_kind = 'league'
    group by 1, 2, 3
    having countif(g.team_sk is null) = 0
),

table_sections as (
    select t.*
    from team_sections as t
    left join combined as c
        on
            t.league_code = c.league_code
            and t.season_api_year = c.season_api_year
            and t.group_name = c.group_name
    where c.group_name is null
),

-- For each team of a section, the other sections of its league-season it sits in that are neither
-- named rankings nor combined tables.
team_elsewhere as (
    select
        a.league_code,
        a.season_api_year,
        a.group_name,
        a.team_sk,
        array_agg(distinct b.group_name ignore nulls) as elsewhere
    from team_sections as a
    left join table_sections as b
        on
            a.league_code = b.league_code
            and a.season_api_year = b.season_api_year
            and a.team_sk = b.team_sk
            and a.group_name != b.group_name
            and b.named_kind != 'ranking'
    group by 1, 2, 3, 4
),

one_team_per_table as (
    select
        league_code,
        season_api_year,
        group_name
    from team_elsewhere
    group by 1, 2, 3
    having
        count(*) >= 2
        and min(array_length(elsewhere)) = 1
        and max(array_length(elsewhere)) = 1
        and count(distinct elsewhere[safe_offset(0)]) = count(*)
),

resolved as (
    select
        n.league_code,
        n.season_api_year,
        n.group_name,
        if(o.group_name is null and c.group_name is null, n.named_kind, 'ranking') as expected_kind
    from named as n
    left join one_team_per_table as o
        on
            n.league_code = o.league_code
            and n.season_api_year = o.season_api_year
            and n.group_name = o.group_name
    left join combined as c
        on
            n.league_code = c.league_code
            and n.season_api_year = c.season_api_year
            and n.group_name = c.group_name
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
