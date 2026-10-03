{#
  Player-match legs aggregated to (team, finished match). This unlocks team-level metrics
  that fct_fixture_team_stats does not provide — tackles, interceptions, blocks, duels,
  dribbles, key passes — by summing the per-player counts. Grain: (fixture_sk, team_sk).

  Inherits the player-stat coverage gaps: where a competition lacks statistics_players,
  no player legs exist and the team has no row here (honest absence, not zero).
  players_with_stats carries the sample so downstream can judge completeness. A total is blank
  where any player row of the team-match has the stat blank: a sum over the rows we happen to
  have would be understated.
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
    if(logical_and(passes_key is not null), sum(passes_key), null) as passes_key,
    if(logical_and(tackles is not null), sum(tackles), null) as tackles,
    if(logical_and(blocks is not null), sum(blocks), null) as blocks,
    if(logical_and(interceptions is not null), sum(interceptions), null) as interceptions,
    if(logical_and(duels is not null), sum(duels), null) as duels,
    if(logical_and(duels_won is not null), sum(duels_won), null) as duels_won,
    if(logical_and(dribbles is not null), sum(dribbles), null) as dribbles,
    if(logical_and(dribbles_success is not null), sum(dribbles_success), null) as dribbles_success,
    if(logical_and(fouls is not null), sum(fouls), null) as fouls,
    if(logical_and(fouls_against is not null), sum(fouls_against), null) as fouls_against
from player_legs
group by fixture_sk, team_sk
