{{ config(materialized='table') }}

{#
  GAP-16 — the player's team per competition-season: the club of their MOST RECENT finished match
  that season (chosen because it is deterministic and byte-stable, where the roster
  affiliation source has no transfer date so cannot give a stable "latest team that season").
  is_current_team flags the single season-row holding the player's globally most-recent finished
  match (their current club). dbt owns "which team is current"; the consumption layer never re-ranks.

  Built on int_legs__player_match (the conformed finished player-match leg; team_sk = the club the
  player played for in that match), mirroring int_player_season_record. Grain:
  (player_sk, league_code, season_api_year) — 1:1 with mart_player_profile's (player_sk, season_sk).
  Consumed only by mart_player_profile.
#}

with legs as (
    select
        player_sk,
        team_sk,
        league_code,
        season_api_year,
        fixture_sk,
        kickoff_datetime
    from {{ ref('int_legs__player_match') }}
),

-- Club of the player's most recent finished match in each competition-season.
season_team as (
    select
        player_sk,
        league_code,
        season_api_year,
        team_sk,
        kickoff_datetime as last_match_kickoff
    from legs
    qualify row_number() over (
        partition by player_sk, league_code, season_api_year
        order by kickoff_datetime desc, fixture_sk desc
    ) = 1
),

-- Rank each competition-season by recency within the player; rank 1 = their current club.
ranked as (
    select
        player_sk,
        league_code,
        season_api_year,
        team_sk,
        row_number() over (
            partition by player_sk
            order by last_match_kickoff desc, season_api_year desc, league_code desc
        ) as current_rank
    from season_team
)

select
    player_sk,
    league_code,
    season_api_year,
    team_sk,
    current_rank = 1 as is_current_team
from ranked
