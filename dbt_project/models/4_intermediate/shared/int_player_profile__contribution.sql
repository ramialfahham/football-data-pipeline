{#
  Player contribution-share — a player's goal-involvement share of the team's WHOLE-SEASON goals
  (content_architecture §6.4, the "bonus" flagship; a player-profile differentiator, sibling of
  int_player_profile__yoy). "Involved in 45% of Bayern's goals."

  Metric definition:
    - numerator = scorer_points_player (goals + assists), its catalogue formula over the player's matches
      for the club that competition-season, written by scripts/generate_metric_sql.py; NULL when a match
      lacks an input or the club has a match with no player data at all.
    - denominator = team_goals_season = the club's goals over ALL its played matches that competition-season
      (the authoritative scoreline; a forfeit's goals, which no player scored, are left out), NOT just the
      matches the player appeared in.
    - contribution_player_pct = scorer_points_player / team_goals_season. Range [0, 1] (a player's G+A over his
      appearances is <= the club's whole-season goals); NULL when the club scored 0 that competition-season.

  A COMPOSING intermediate: it reuses the leg atoms, never recomputing them (mirrors
  int_team_season__deserved_vs_actual). season_sk is inherited from the team leg. NOT domestic-restricted —
  the ratio is valid in any competition and self-restricts to where player-stat data exists (no player leg ->
  no numerator -> no row).

  Grain: (player_sk, team_sk, season_sk) — one row per player's club-competition-season; a mid-season transfer
  yields two rows. mart_player_profile attaches the player's primary-club row.
#}

with player_legs as (
    select
        player_sk,
        team_sk,
        fixture_sk,
        goals,
        assists
    from {{ ref('int_legs__player_match') }}
),

team_legs as (
    select
        team_sk,
        season_sk,
        league_code,
        season_api_year,
        fixture_sk,
        goals,
        is_awarded_result
    from {{ ref('int_legs__team_match') }}
),

-- A team match with no player data at all: nobody knows who played or what they did, so every player
-- metric of that team is blank for any window that contains it. Awarded results are no match played.
team_seasons_without_player_data as (
    select distinct
        tl.team_sk,
        tl.season_sk
    from team_legs as tl
    left join {{ ref('int_legs__team_from_players') }} as tp
        on tl.fixture_sk = tp.fixture_sk and tl.team_sk = tp.team_sk
    where not tl.is_awarded_result and tp.fixture_sk is null
),

-- The join to the team leg on (fixture_sk, team_sk) supplies season_sk and confirms the finished team match.
window_rows as (
    select
        pl.*,
        tl.season_sk,
        tl.league_code,
        tl.season_api_year,
        uncovered.team_sk is null as window_is_complete
    from player_legs as pl
    inner join team_legs as tl
        on pl.fixture_sk = tl.fixture_sk and pl.team_sk = tl.team_sk
    left join team_seasons_without_player_data as uncovered
        on tl.team_sk = uncovered.team_sk and tl.season_sk = uncovered.season_sk
),

involvements as (
    select
        player_sk,
        team_sk,
        season_sk,
        any_value(league_code) as league_code,
        any_value(season_api_year) as season_api_year,
        -- metric sql generated from metric_catalogue.csv by scripts/generate_metric_sql.py; edit the catalogue
        if(
            logical_and(window_is_complete and (goals + assists) is not null),
            sum(goals + assists),
            null
        ) as scorer_points_player
        -- end of generated metric sql
    from window_rows
    group by player_sk, team_sk, season_sk
),

-- Denominator: the club's whole-season goals (all its played matches that competition-season).
team_goals as (
    select
        team_sk,
        season_sk,
        sum(if(is_awarded_result, null, goals)) as team_goals_season
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
