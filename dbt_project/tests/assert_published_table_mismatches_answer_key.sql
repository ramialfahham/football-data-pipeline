{#
  Hand-written answer key for the macro published_table_mismatches. Each published section is one
  (group, ingest time); the macro must return exactly the teams listed under "expected". The columns
  of a row: published place, rebuilt place, published points, rebuilt points, place not compared,
  section comparable. The teams listed in "compared" as withheld are the withheld team-seasons.

  A  four teams, places and points agree                               -> nothing
  B  all points agree, teams 1 and 2 swapped                           -> teams 1 and 2
  C  team 3 is withheld and its points differ, which moves it down     -> nothing: the others keep their order
  D  team 3 is withheld, teams 1 and 2 swapped                         -> teams 1 and 2
  E  teams 2 and 3 are level and the rule does not fix their order     -> nothing (they are left out of the place comparison)
  F  a section that is not comparable, teams swapped                   -> nothing
  G  team 2 has no rebuilt place, the others agree                     -> nothing
  H  the provider gives teams 1 and 2 the same place, ours 1 and 2     -> team 2
  I  two groups at one ingest time, one agrees, the other swapped      -> the swapped group's teams 1 and 2
  J  team 1 has no published place, teams 2 and 3 agree                -> nothing
  K  teams 2 and 3 are level and not compared, team 4 sits above them  -> team 4 (the level teams keep their places)
  L  team 2 is not withheld and its points are off by 1, places agree  -> team 2
  M  the same as L with team 2 withheld                                -> nothing
  N  the same as L in a section that is not comparable                 -> nothing
  O  team 1 has no published place and its points are off by 1         -> team 1
  P  teams 2 and 3 have no rebuilt place, team 1 is placed 3 not 1     -> team 1 (a place error next to teams with no place is red)
  Q  team 1 is withheld above teams 2 and 3, which move up by one      -> nothing (on the published side by one, on the rebuilt side by none)
  R  team 1 is withheld and shares the published place 1 with team 2   -> nothing (a tie is not above)

  Returns every case where the macro's rows differ from the expected rows.
#}
{{ config(store_failures = true, severity = 'error') }}

with compared_rows as (
    select * from unnest([
        struct(
            'XX' as league_code,
            2025 as season_api_year,
            'A' as group_name,
            timestamp('2025-01-01') as ingested_at,
            1 as team_sk,
            1 as published_rank,
            1 as rebuilt_rank,
            9 as published_points,
            9 as rebuilt_points,
            false as is_place_not_compared,
            true as is_comparable
        ),
        ('XX', 2025, 'A', timestamp('2025-01-01'), 2, 2, 2, 6, 6, false, true),
        ('XX', 2025, 'A', timestamp('2025-01-01'), 3, 3, 3, 3, 3, false, true),
        ('XX', 2025, 'A', timestamp('2025-01-01'), 4, 4, 4, 1, 1, false, true),

        ('XX', 2025, 'B', timestamp('2025-01-02'), 1, 1, 2, 9, 9, false, true),
        ('XX', 2025, 'B', timestamp('2025-01-02'), 2, 2, 1, 9, 9, false, true),
        ('XX', 2025, 'B', timestamp('2025-01-02'), 3, 3, 3, 3, 3, false, true),
        ('XX', 2025, 'B', timestamp('2025-01-02'), 4, 4, 4, 1, 1, false, true),

        ('XX', 2025, 'C', timestamp('2025-01-03'), 1, 1, 1, 9, 9, false, true),
        ('XX', 2025, 'C', timestamp('2025-01-03'), 2, 2, 2, 6, 6, false, true),
        ('XX', 2025, 'C', timestamp('2025-01-03'), 3, 3, 4, 5, 3, false, true),
        ('XX', 2025, 'C', timestamp('2025-01-03'), 4, 4, 3, 3, 3, false, true),

        ('XX', 2025, 'D', timestamp('2025-01-04'), 1, 1, 2, 9, 9, false, true),
        ('XX', 2025, 'D', timestamp('2025-01-04'), 2, 2, 1, 9, 9, false, true),
        ('XX', 2025, 'D', timestamp('2025-01-04'), 3, 3, 3, 5, 3, false, true),
        ('XX', 2025, 'D', timestamp('2025-01-04'), 4, 4, 4, 1, 1, false, true),

        ('XX', 2025, 'E', timestamp('2025-01-05'), 1, 1, 1, 9, 9, false, true),
        ('XX', 2025, 'E', timestamp('2025-01-05'), 2, 2, 3, 6, 6, true, true),
        ('XX', 2025, 'E', timestamp('2025-01-05'), 3, 3, 2, 6, 6, true, true),
        ('XX', 2025, 'E', timestamp('2025-01-05'), 4, 4, 4, 3, 3, false, true),

        ('XX', 2025, 'F', timestamp('2025-01-06'), 1, 1, 2, 9, 9, false, false),
        ('XX', 2025, 'F', timestamp('2025-01-06'), 2, 2, 1, 9, 9, false, false),

        ('XX', 2025, 'G', timestamp('2025-01-07'), 1, 1, 1, 9, 9, false, true),
        ('XX', 2025, 'G', timestamp('2025-01-07'), 2, 2, cast(null as int64), 6, 6, false, true),
        ('XX', 2025, 'G', timestamp('2025-01-07'), 3, 3, 3, 3, 3, false, true),
        ('XX', 2025, 'G', timestamp('2025-01-07'), 4, 4, 4, 1, 1, false, true),

        ('XX', 2025, 'H', timestamp('2025-01-08'), 1, 1, 1, 9, 9, false, true),
        ('XX', 2025, 'H', timestamp('2025-01-08'), 2, 1, 2, 9, 9, false, true),
        ('XX', 2025, 'H', timestamp('2025-01-08'), 3, 3, 3, 3, 3, false, true),

        ('XX', 2025, 'I1', timestamp('2025-01-09'), 1, 1, 1, 9, 9, false, true),
        ('XX', 2025, 'I1', timestamp('2025-01-09'), 2, 2, 2, 6, 6, false, true),
        ('XX', 2025, 'I2', timestamp('2025-01-09'), 1, 1, 2, 9, 9, false, true),
        ('XX', 2025, 'I2', timestamp('2025-01-09'), 2, 2, 1, 9, 9, false, true),

        ('XX', 2025, 'J', timestamp('2025-01-10'), 1, cast(null as int64), 3, 9, 9, false, true),
        ('XX', 2025, 'J', timestamp('2025-01-10'), 2, 1, 1, 9, 9, false, true),
        ('XX', 2025, 'J', timestamp('2025-01-10'), 3, 2, 2, 6, 6, false, true),

        ('XX', 2025, 'K', timestamp('2025-01-11'), 1, 1, 1, 9, 9, false, true),
        ('XX', 2025, 'K', timestamp('2025-01-11'), 2, 2, 3, 6, 6, true, true),
        ('XX', 2025, 'K', timestamp('2025-01-11'), 3, 3, 4, 6, 6, true, true),
        ('XX', 2025, 'K', timestamp('2025-01-11'), 4, 4, 2, 4, 4, false, true),
        ('XX', 2025, 'K', timestamp('2025-01-11'), 5, 5, 5, 3, 3, false, true),

        ('XX', 2025, 'L', timestamp('2025-01-12'), 1, 1, 1, 9, 9, false, true),
        ('XX', 2025, 'L', timestamp('2025-01-12'), 2, 2, 2, 6, 5, false, true),
        ('XX', 2025, 'L', timestamp('2025-01-12'), 3, 3, 3, 3, 3, false, true),

        ('XX', 2025, 'M', timestamp('2025-01-13'), 1, 1, 1, 9, 9, false, true),
        ('XX', 2025, 'M', timestamp('2025-01-13'), 2, 2, 2, 6, 5, false, true),
        ('XX', 2025, 'M', timestamp('2025-01-13'), 3, 3, 3, 3, 3, false, true),

        ('XX', 2025, 'N', timestamp('2025-01-14'), 1, 1, 1, 9, 9, false, false),
        ('XX', 2025, 'N', timestamp('2025-01-14'), 2, 2, 2, 6, 5, false, false),
        ('XX', 2025, 'N', timestamp('2025-01-14'), 3, 3, 3, 3, 3, false, false),

        ('XX', 2025, 'O', timestamp('2025-01-15'), 1, cast(null as int64), 1, 9, 8, false, true),
        ('XX', 2025, 'O', timestamp('2025-01-15'), 2, 2, 2, 6, 6, false, true),

        ('XX', 2025, 'P', timestamp('2025-01-16'), 1, 1, 3, 9, 9, false, true),
        ('XX', 2025, 'P', timestamp('2025-01-16'), 2, 2, cast(null as int64), 9, 9, false, true),
        ('XX', 2025, 'P', timestamp('2025-01-16'), 3, 3, cast(null as int64), 9, 9, false, true),
        ('XX', 2025, 'P', timestamp('2025-01-16'), 4, 4, 4, 3, 3, false, true),

        ('XX', 2025, 'Q', timestamp('2025-01-17'), 1, 1, 3, 9, 3, false, true),
        ('XX', 2025, 'Q', timestamp('2025-01-17'), 2, 2, 1, 6, 6, false, true),
        ('XX', 2025, 'Q', timestamp('2025-01-17'), 3, 3, 2, 3, 3, false, true),

        ('XX', 2025, 'R', timestamp('2025-01-18'), 1, 1, 1, 9, 3, false, true),
        ('XX', 2025, 'R', timestamp('2025-01-18'), 2, 1, 2, 9, 9, false, true),
        ('XX', 2025, 'R', timestamp('2025-01-18'), 3, 3, 3, 3, 3, false, true)
    ])
),

compared as (
    select
        *,
        concat(group_name, ':', cast(team_sk as string)) in ('C:3', 'D:3', 'M:2', 'Q:1', 'R:1') as is_withheld
    from compared_rows
),

expected as (
    select * from unnest([
        struct('B' as group_name, 1 as team_sk),
        ('B', 2),
        ('D', 1),
        ('D', 2),
        ('H', 2),
        ('I2', 1),
        ('I2', 2),
        ('K', 4),
        ('L', 2),
        ('O', 1),
        ('P', 1)
    ])
),

found as (
    {{ published_table_mismatches('compared') }}
)

select
    coalesce(f.group_name, e.group_name) as group_name,
    coalesce(f.team_sk, e.team_sk) as team_sk,
    f.team_sk is not null as returned,
    e.team_sk is not null as expected
from found as f
full outer join expected as e
    on f.group_name = e.group_name and f.team_sk = e.team_sk
where f.team_sk is null or e.team_sk is null
