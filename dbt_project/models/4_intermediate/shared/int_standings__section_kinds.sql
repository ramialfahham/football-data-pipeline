{#
  What kind of table each standings section is: one row per distinct section name in
  fct_standings, with the kind of the lowest-priority standings_table_kinds pattern that matches
  it (ranking, split_round, group, conference), and league where none does. mart_standings and
  int_team_season__table_by_time read it, so a section has one kind everywhere.

  Grain: (group_name).
#}

with sections as (
    select distinct group_name
    from {{ ref('fct_standings') }}
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
    from sections as s
    cross join kind_patterns as k
    where regexp_contains(lower(s.group_name), k.pattern)
    qualify row_number() over (partition by s.group_name order by k.priority) = 1
)

select
    s.group_name,
    coalesce(m.table_kind, 'league') as table_kind
from sections as s
left join matched as m
    on s.group_name = m.group_name
