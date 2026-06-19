{{ config(materialized='view') }}

{#
  mart_roster — identity-only club squad list (the Squad block; content_architecture §3).
  One row per rostered player per (club team, competition-season), from
  dim_player_team_season_mapping joined to dim_player for identity. Scoped to CLUB
  competitions (entity_type = 'club', resolved league_code -> competition_registry ->
  competition_types — mirrors mart_standings; never a dim_team flag, per the
  dim_team-is-a-pure-entity ruling).

  Identity only: name, listed position, nationality, birth_date, photo. NO per-club season
  stats / appearances — that is the deferred per-club grain (#480 §8.3). Age is a render-time
  derivation, so the mart carries player_birth_date, not a (non-deterministic) stored age.

  dim_player is LEFT-joined so a membership with no resolvable player entity is NOT silently
  dropped — it surfaces through the player_sk -> dim_player relationships test instead.

  league_code is the partition key. season_sk is nullable (a roster season with no
  competition-season row in dim_competition_season); season_api_year is always present and
  anchors the grain. Grain: (team_sk, league_code, season_api_year, player_sk).
#}

with mapping as (
    select * from {{ ref('dim_player_team_season_mapping') }}
),

players as (
    select * from {{ ref('dim_player') }}
),

registry as (
    select
        league_code,
        competition_type
    from {{ ref('competition_registry') }}
),

types as (
    select
        competition_type,
        entity_type
    from {{ ref('competition_types') }}
)

select
    m.player_team_season_sk,
    m.team_sk,
    m.player_sk,
    m.season_sk,
    m.league_code,
    m.season_api_year,
    reg.competition_type,
    typ.entity_type,
    p.player_name,
    p.player_position,
    p.player_nationality,
    p.player_birth_date,
    p.player_photo_url
from mapping as m
left join players as p
    on m.player_sk = p.player_sk
left join registry as reg
    on m.league_code = reg.league_code
left join types as typ
    on reg.competition_type = typ.competition_type
where typ.entity_type = 'club'
