{#
  What kind of table each standings section of a league-season is: ranking, split_round, group,
  conference or league. The kind is the lowest-priority standings_table_kinds pattern that matches
  the section's name, and league where none does. A section is also a ranking when it holds one
  team from each of the league-season's other tables: every team in it sits in exactly one other
  section that is not a ranking, and no two of its teams in the same one. mart_standings,
  int_team_season__table_state and int_team_season__standings_primary read it, so a section has
  one kind everywhere.

  Grain: (league_code, season_api_year, group_name).
#}

with section_teams as (
    select distinct
        league_code,
        season_api_year,
        group_name,
        team_sk
    from {{ ref('fct_standings') }}
),

sections as (
    select distinct
        league_code,
        season_api_year,
        group_name
    from section_teams
),

kind_patterns as (
    select
        priority,
        pattern,
        table_kind
    from {{ ref('standings_table_kinds') }}
),

matched as (
    select
        s.group_name,
        k.table_kind
    from (select distinct group_name from sections) as s
    cross join kind_patterns as k
    where regexp_contains(lower(s.group_name), k.pattern)
    qualify row_number() over (partition by s.group_name order by k.priority) = 1
),

named_kinds as (
    select
        s.league_code,
        s.season_api_year,
        s.group_name,
        coalesce(m.table_kind, 'league') as table_kind
    from sections as s
    left join matched as m
        on s.group_name = m.group_name
),

table_teams as (
    select t.*
    from section_teams as t
    inner join named_kinds as k
        on
            t.league_code = k.league_code
            and t.season_api_year = k.season_api_year
            and t.group_name = k.group_name
    where k.table_kind != 'ranking'
),

team_other_tables as (
    select
        s.league_code,
        s.season_api_year,
        s.group_name,
        s.team_sk,
        count(o.group_name) as other_tables,
        min(o.group_name) as other_table
    from section_teams as s
    left join table_teams as o
        on
            s.league_code = o.league_code
            and s.season_api_year = o.season_api_year
            and s.team_sk = o.team_sk
            and s.group_name != o.group_name
    group by s.league_code, s.season_api_year, s.group_name, s.team_sk
),

cross_group_rankings as (
    select
        league_code,
        season_api_year,
        group_name
    from team_other_tables
    group by league_code, season_api_year, group_name
    having
        count(*) > 1
        and logical_and(other_tables = 1)
        and count(distinct other_table) = count(*)
)

select
    k.league_code,
    k.season_api_year,
    k.group_name,
    if(r.group_name is null, k.table_kind, 'ranking') as table_kind
from named_kinds as k
left join cross_group_rankings as r
    on
        k.league_code = r.league_code
        and k.season_api_year = r.season_api_year
        and k.group_name = r.group_name
