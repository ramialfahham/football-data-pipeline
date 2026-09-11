{{ config(materialized='table') }}

{#
  Dated player transfers (moves). One row per distinct move: which player moved from
  which team to which team, on which date, plus the provider's raw type string. The
  dated source of the player affiliation timeline (valid_from / valid_to and the
  chronological order are derived downstream).

  player_sk is the API player id (= dim_player.player_sk); team_in_sk / team_out_sk are
  API team ids (= dim_team.team_sk). team_in_sk or team_out_sk may be null when the
  provider omits a side of the move. No relationship tests to dim_player / dim_team:
  transfers legitimately reference clubs and players outside our covered competitions.

  league_code is INGEST PROVENANCE (the tracked league whose team pull surfaced the move,
  pinned deterministically in base), NOT a semantic partition — a transfer is a global player
  event. Do not filter affiliation by league_code expecting completeness.

  Grain: (player_sk, team_out_sk, team_in_sk, transfer_date).
#}

with src as (
    select * from {{ ref('base_apif__transfers') }}
)

select
    {{ dbt_utils.generate_surrogate_key([
        'player_id',
        'team_in_id',
        'team_out_id',
        'transfer_date'
    ]) }} as transfer_sk,
    cast(player_id as int64) as player_sk,
    cast(team_in_id as int64) as team_in_sk,
    cast(team_out_id as int64) as team_out_sk,
    transfer_date,
    transfer_type,
    league_code,
    raw_ingested_at
from src
