{{ config(materialized='table') }}

{#
  W1 last-5 momentum mart — team.

  Computes final displayed metrics from the raw sums in int_momentum__team.
  All divisions live here — none in the builder. Returns NULL for any metric
  whose denominator is zero (safe_divide).

  Grain: (upcoming_fixture_sk, team_sk).

  league_rank is not computed here — it comes from the standings surface (#322).
  player-derived metrics (key_passes_per_match through dribbles_success_pct) are
  NULL when no player stats exist for the window (coverage gap, honest absence).
#}

with builder as (
    select * from {{ ref('int_momentum__team') }}
),

fixtures as (
    select
        fixture_sk,
        league_code,
        home_team_sk
    from {{ ref('fct_fixture') }}
)

select
    b.upcoming_fixture_sk,
    b.team_sk,
    f.league_code,
    b.entity_type,
    b.season_api_year,
    b.window_type,
    b.games_in_window,
    b.games_with_team_stats,
    b.contributing_competitions,
    b.games_with_player_stats,
    b.points_won,
    -- clean sheets: scoreline-based count, displays as x of games_in_window
    b.clean_sheet_games as clean_sheets,
    b.team_sk = f.home_team_sk as is_home,
    -- goals (scoreline — always present, divide over the full window)
    safe_divide(b.goals_for, b.games_in_window) as goals_per_match,
    safe_divide(b.goals_against, b.games_in_window) as goals_against_per_match,
    -- shots (team-stat window)
    safe_divide(b.shots_total, b.games_with_team_stats) as shots_per_match,
    safe_divide(b.shots_on_goal, b.shots_total) as shot_accuracy,
    safe_divide(b.shots_inside_box, b.shots_total) as danger_zone_ratio,
    safe_divide(b.shots_on_goal, b.games_with_team_stats)
        as shots_on_target_per_match,
    -- finishing: goals restricted to shot-covered games keeps it same-window
    safe_divide(b.goals_for_in_shot_games, b.shots_on_goal)
        as finishing_efficiency,
    -- passing (team-stat window)
    safe_divide(b.passes_total, b.games_with_team_stats) as passes_per_match,
    safe_divide(b.passes_accurate, b.passes_total) as pass_accuracy,
    -- set pieces (team-stat window; conceded uses opponent-stat coverage)
    safe_divide(b.corner_kicks, b.games_with_team_stats) as corner_kicks_per_match,
    safe_divide(b.opponent_corner_kicks, b.games_with_opp_stats)
        as corners_conceded_per_match,
    -- goalkeeper: saves / (saves + goals conceded in save-covered games); self-bounded
    safe_divide(b.goalkeeper_saves, b.goalkeeper_saves + b.goals_against_in_save_games)
        as save_ratio,
    -- player-derived team metrics (player-stat window; null when unavailable)
    safe_divide(b.key_passes, b.games_with_player_stats) as key_passes_per_match,
    safe_divide(b.tackles, b.games_with_player_stats) as tackles_per_match,
    safe_divide(b.interceptions, b.games_with_player_stats)
        as interceptions_per_match,
    safe_divide(b.blocks, b.games_with_player_stats) as blocks_per_match,
    -- T+I+B share one coverage window (same player rows), so the sum is
    -- same-window by construction; null when any input is null (no coverage)
    safe_divide(b.tackles + b.interceptions + b.blocks, b.games_with_player_stats)
        as defensive_actions_per_match,
    safe_divide(b.duels_total, b.games_with_player_stats) as duels_per_match,
    safe_divide(b.duels_won, b.duels_total) as duels_won_pct,
    safe_divide(b.dribbles_success, b.dribbles_attempts) as dribbles_success_pct
from builder as b
inner join fixtures as f
    on b.upcoming_fixture_sk = f.fixture_sk
