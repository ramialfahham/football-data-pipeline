{{ config(materialized='table') }}

{#
  Player Career tab (content_architecture §4): one row per (player, competition) with the player's CAREER
  totals in that competition (int_player_career__metrics) + identity (dim_player) + the competition's
  entity_type (club / national, via the registry -> competition_types seeds).

  National-entity rows are the player's NATIONAL APPEARANCES IN COVERED COMPETITIONS — honestly NOT true
  career caps: we ingest only a subset of national competitions, so this undercounts a player's full
  international history. national_appearances_total denormalises the per-player national-appearance sum so
  the export reads it directly (a fact computed in dbt, never derived in the consumption layer).

  The clubs-played-for list is served by dim_player_team_season_mapping, not duplicated here.
  Grain: (player_sk, league_code).
#}

with career as (
    select * from {{ ref('int_player_career__metrics') }}
),

players as (
    select
        player_sk,
        player_name,
        player_nationality,
        player_photo_url
    from {{ ref('dim_player') }}
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
),

career_typed as (
    select
        career.player_career_sk,
        career.player_sk,
        career.league_sk,
        career.league_code,
        career.seasons_played,
        career.first_season,
        career.last_season,
        career.appearances,
        career.goals,
        career.assists,
        types.entity_type
    from career
    left join registry on career.league_code = registry.league_code
    left join types on registry.competition_type = types.competition_type
)

select
    ct.player_career_sk,
    ct.player_sk,
    p.player_name,
    p.player_nationality,
    p.player_photo_url,
    ct.league_code,
    ct.league_sk,
    ct.entity_type,
    ct.seasons_played,
    ct.first_season,
    ct.last_season,
    ct.appearances,
    ct.goals,
    ct.assists,
    sum(case when ct.entity_type = 'national' then ct.appearances else 0 end)
        over (partition by ct.player_sk) as national_appearances_total
from career_typed as ct
left join players as p on ct.player_sk = p.player_sk
