{{ config(materialized='table') }}

{#
  Player contribution-share — a player's goal-involvement share of the team's WHOLE-SEASON goals
  (content_architecture §6.4, the "bonus" flagship; a player-profile differentiator, sibling of
  int_player_profile__yoy). "Involved in 45% of Bayern's goals."

  Metric definition:
    - numerator = scorer_points_player = goals_total + goals_assists (summed over the player's appearances-with-stats)
    - denominator = team_goals_season = the club's goals_for over ALL its matches that competition-season (the
      authoritative scoreline), NOT just the matches the player appeared in.
    - contribution_player_pct = scorer_points_player / team_goals_season. Range [0, 1] (a player's G+A over his
      appearances is <= the club's whole-season goals); NULL when the club scored 0 that competition-season.

  Honest limit, accepted by design: player stats are sparse (many matches lack statistics_players). Where the
  player's stats are missing for a game he played, his involvements there go uncounted while the whole-season
  denominator stays complete — so the share UNDERSTATES for players with coverage gaps. Absence is honest.

  A COMPOSING intermediate: it reuses the leg atoms, never recomputing them (mirrors
  int_team_season__deserved_vs_actual). season_sk is inherited from the team leg (the player leg carries only
  season_api_year + league_code). NOT domestic-restricted — the ratio is valid in any competition and
  self-restricts to where player-stat data exists (no player leg -> no numerator -> no row).

  Grain: (player_sk, team_sk, season_sk) — one row per player's club-competition-season; a mid-season transfer
  yields two rows. mart_player_profile attaches the player's primary-club row.
#}

with player_legs as (
    select
        player_sk,
        team_sk,
        fixture_sk,
        goals_total,
        goals_assists
    from {{ ref('int_legs__player_match') }}
),

team_legs as (
    select
        team_sk,
        season_sk,
        league_code,
        season_api_year,
        fixture_sk,
        goals_for
    from {{ ref('int_legs__team_match') }}
),

-- Numerator: the player's goal involvements per (player, club, competition-season). The join to the team leg
-- on (fixture_sk, team_sk) supplies season_sk (absent on the player leg) and confirms the finished team match.
involvements as (
    select
        pl.player_sk,
        pl.team_sk,
        tl.season_sk,
        any_value(tl.league_code) as league_code,
        any_value(tl.season_api_year) as season_api_year,
        sum(pl.goals_total + pl.goals_assists) as scorer_points_player
    from player_legs as pl
    inner join team_legs as tl
        on pl.fixture_sk = tl.fixture_sk and pl.team_sk = tl.team_sk
    group by pl.player_sk, pl.team_sk, tl.season_sk
),

-- Denominator: the club's whole-season goals_for (all its matches that competition-season).
team_goals as (
    select
        team_sk,
        season_sk,
        sum(goals_for) as team_goals_season
    from team_legs
    group by team_sk, season_sk
)

select
    inv.player_sk,
    inv.team_sk,
    inv.season_sk,
    inv.league_code,
    inv.season_api_year,
    inv.scorer_points_player,
    tg.team_goals_season,
    safe_divide(inv.scorer_points_player, tg.team_goals_season) as contribution_player_pct
from involvements as inv
inner join team_goals as tg
    on inv.team_sk = tg.team_sk and inv.season_sk = tg.season_sk
