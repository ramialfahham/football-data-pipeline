{{ config(materialized='table') }}

{#
  Player-match legs aggregated to (team, finished match). This unlocks team-level metrics
  that fct_fixture_team_stats does not provide — tackles, interceptions, blocks, duels,
  dribbles, key passes — by summing the per-player counts. Grain: (fixture_sk, team_sk).

  Inherits the player-stat coverage gaps: where a competition lacks statistics_players,
  no player legs exist and the team has no row here (honest absence, not zero).
  players_with_stats carries the sample so downstream can judge completeness.
#}

with player_legs as (
    select * from {{ ref('int_legs__player_match') }}
)

select
    fixture_sk,
    team_sk,
    any_value(league_code) as league_code,
    any_value(season_api_year) as season_api_year,
    any_value(competition_type) as competition_type,
    any_value(entity_type) as entity_type,
    any_value(kickoff_datetime) as kickoff_datetime,
    any_value(round_order) as round_order,
    any_value(opponent_team_sk) as opponent_team_sk,
    count(*) as players_with_stats,
    sum(passes_key) as key_passes,
    sum(tackles_total) as tackles,
    sum(tackles_blocks) as blocks,
    sum(tackles_interceptions) as interceptions,
    sum(duels_total) as duels_total,
    sum(duels_won) as duels_won,
    sum(dribbles_attempts) as dribbles_attempts,
    sum(dribbles_success) as dribbles_success,
    sum(fouls_committed) as fouls_committed,
    sum(fouls_drawn) as fouls_drawn
from player_legs
group by fixture_sk, team_sk
