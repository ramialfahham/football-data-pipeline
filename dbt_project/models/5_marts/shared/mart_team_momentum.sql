{{ config(materialized='table') }}

{#
  W1 momentum mart — team.

  Computes final displayed metrics from the raw sums in int_team_momentum__metrics. The window
  is last-5 for most competitions and cumulative for tournament fixtures (window_type,
  GAP-18); every rate divides over games_in_window or the matching coverage count, so it
  is correct for any window size. All divisions live here — none in the builder. Returns
  NULL for any metric whose denominator is zero (safe_divide).

  Grain: (upcoming_fixture_sk, team_sk).

  league_rank is not computed here — it comes from the standings surface (#322).
  player-derived metrics (key_passes_per_match through duels_won_pct) are
  NULL when no player stats exist for the window (coverage gap, honest absence).
#}

with builder as (
    select * from {{ ref('int_team_momentum__metrics') }}
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
    -- shots (team-stat window): NULL ('—') on partial coverage — never a partial-window average
    -- (reverse #320; universal incomplete-data rule, CPO 2026-06-25). shots_on_goal_pct / danger_zone
    -- gate on the binding shot coverage (SoT ⊆ team-stat, so full SoT coverage ⇒ full shots_total).
    case
        when b.games_with_team_stats < b.games_in_window then null
        else safe_divide(b.shots_total, b.games_with_team_stats)
    end as shots_per_match,
    case
        when b.games_with_sot_stats < b.games_in_window then null
        else safe_divide(b.shots_on_goal, b.shots_total)
    end as shots_on_goal_pct,
    case
        when b.games_with_team_stats < b.games_in_window then null
        else safe_divide(b.shots_inside_box, b.shots_total)
    end as shots_inside_box_pct,
    case
        when b.games_with_sot_stats < b.games_in_window then null
        else safe_divide(b.shots_on_goal, b.games_with_sot_stats) end
        as shots_on_goal_per_match,
    -- finishing efficiency (CPO Option A): open-play conversion =
    -- (goals_for − goals_penalty − goals_own) / shots_on_goal. NULL ('—') unless the window is
    -- fully shot-covered AND the numerator is valid [0, shots_on_goal] — never a partial-window
    -- value and never >100% (penalties + own goals removed; a stray inconsistency nulls out).
    case
        when b.games_with_sot_stats < b.games_in_window then null
        when (b.goals_for - b.goals_penalty - b.goals_own) < 0 then null
        when (b.goals_for - b.goals_penalty - b.goals_own) > b.shots_on_goal then null
        else safe_divide(b.goals_for - b.goals_penalty - b.goals_own, b.shots_on_goal)
    end as finishing_efficiency,
    -- passing (team-stat window): NULL on partial coverage
    case
        when b.games_with_team_stats < b.games_in_window then null
        else safe_divide(b.passes_total, b.games_with_team_stats)
    end as passes_per_match,
    case
        when b.games_with_team_stats < b.games_in_window then null
        else safe_divide(b.passes_accurate, b.passes_total)
    end as pass_accuracy,
    -- set pieces (team-stat window; conceded uses opponent-stat coverage): NULL on partial coverage
    case
        when b.games_with_team_stats < b.games_in_window then null
        else safe_divide(b.corner_kicks, b.games_with_team_stats)
    end as corners_per_match,
    case
        when b.games_with_opp_stats < b.games_in_window then null
        else safe_divide(b.opponent_corner_kicks, b.games_with_opp_stats) end
        as corners_against_per_match,
    -- goalkeeper: saves / (saves + goals conceded in save-covered games); self-bounded.
    -- NULL on partial save coverage (the new games_with_save_stats).
    case
        when b.games_with_save_stats < b.games_in_window then null
        else safe_divide(
            b.goalkeeper_saves, b.goalkeeper_saves + b.goals_against_in_save_games
        )
    end as saves_pct,
    -- player-derived team metrics: DELIBERATELY left on average-over-player-covered games (NOT
    -- gated) — these are player data, and missing player stats must not blank a team stat
    -- (CPO 2026-06-25). null only when no player-covered game exists (safe_divide by 0).
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
    safe_divide(b.duels_won, b.duels_total) as duels_won_pct
from builder as b
inner join fixtures as f
    on b.upcoming_fixture_sk = f.fixture_sk
