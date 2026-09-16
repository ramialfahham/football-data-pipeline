{{ config(materialized='view') }}

{#
  Generic standings mart — one approach for every competition that has standings.
  Serves two jobs:
    1. The competition's own table — league table (domestic_league, one section) or
       group tables (group stages of continental/world/qualifying, one section per
       group). Knockout/super/friendly competitions have no standings and are simply
       absent from fct_standings.
    2. A club's domestic-league standing as context on any club fixture — filter to
       competition_type = 'domestic_league' for one row per (club, season) = its
       home-league position.

  Every value is the provider's official standings row as published — rank, points, W/D/L,
  goals scored and conceded, goal difference, form. Nothing here is computed from fixtures: the
  official table carries deductions and tie-break orders a recomputation cannot reproduce, so it
  is a fact from the source, like a match score. NO zones — the provider's zone annotation is
  carried verbatim in group_description and never interpreted.

  table_kind says what kind of table a section is (league, group, conference, split_round,
  ranking), resolved from the section name through the standings_table_kinds seed so that a
  page can render one table per group, drop the provider's cross-group ranking tables and head
  a split season's rounds — and never matches on a name itself. A name no seed pattern matches
  is the competition's own league table.

  league_code discriminates the competition and is not a BigQuery partition or cluster key;
  competition_type / entity_type come from the registry + types seeds. Lives in shared/
  because the output shape is uniform across competition types.

  Grain: (league_code, season_api_year, group_name, team_sk).
#}

with standings as (
    select * from {{ ref('fct_standings') }}
),

registry as (
    select * from {{ ref('competition_registry') }}
),

types as (
    select * from {{ ref('competition_types') }}
),

teams as (
    select
        team_sk,
        team_name,
        team_logo_url
    from {{ ref('dim_team') }}
),

kind_patterns as (
    select
        priority,
        pattern,
        table_kind
    from {{ ref('standings_table_kinds') }}
),

-- One kind per distinct section name: the lowest-priority pattern that matches it.
section_kinds as (
    select
        group_name,
        table_kind
    from (
        select distinct
            s.group_name,
            k.table_kind,
            k.priority
        from standings as s
        cross join kind_patterns as k
        where regexp_contains(lower(s.group_name), k.pattern)
    )
    qualify row_number() over (partition by group_name order by priority) = 1
)

select
    s.standing_sk,
    s.league_code,
    s.season_sk,
    s.season_api_year,
    s.group_name,
    reg.competition_type,
    typ.entity_type,
    s.team_sk,
    s.team_api_id,
    t.team_name,
    t.team_logo_url,
    s.standing_rank,
    s.points,
    s.goals_scored,
    s.goals_conceded,
    s.goals_diff,
    s.form,
    s.played,
    s.wins,
    s.draws,
    s.losses,
    s.group_description,
    coalesce(k.table_kind, 'league') as table_kind
from standings as s
left join registry as reg
    on s.league_code = reg.league_code
left join types as typ
    on reg.competition_type = typ.competition_type
left join teams as t
    on s.team_sk = t.team_sk
left join section_kinds as k
    on s.group_name = k.group_name
