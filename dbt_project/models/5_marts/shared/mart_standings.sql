{{ config(materialized='view') }}

{#
  Generic standings mart — one approach for every competition that has standings.
  Serves both #322 jobs:
    1. The competition's own table — league table (domestic_league, one section) or
       group tables (group stages of continental/world/qualifying, one section per
       group). Knockout/super/friendly competitions have no standings and are simply
       absent from fct_standings.
    2. A club's domestic-league standing as context on any club fixture — filter to
       competition_type = 'domestic_league' for one row per (club, season) = its
       home-league position.

  Type-agnostic: group tables differ from league tables only by group_name being a
  group rather than the league name (see fct_standings). NO zones — rank, points,
  form, W/D/L only (the reliable API fields); zone meaning is deferred (#322 issue).

  league_code is the partition key; competition_type / entity_type come from the
  registry + types seeds. Lives in shared/ because the output shape is uniform across
  competition types.

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
    s.goals_diff,
    s.form,
    s.played,
    s.wins,
    s.draws,
    s.losses,
    s.group_description
from standings as s
left join registry as reg
    on s.league_code = reg.league_code
left join types as typ
    on reg.competition_type = typ.competition_type
left join teams as t
    on s.team_sk = t.team_sk
