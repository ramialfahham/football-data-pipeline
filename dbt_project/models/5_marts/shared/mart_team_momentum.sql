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
  Every rate is NULL unless each input it reads is present in every non-awarded leg of
  the window; the player-derived rates (passes_key_per_match through duels_won_pct)
  read the player feed, so a leg without it blanks them like a missing team stat.
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
    -- the window's games that COULD carry a stat line — games_in_window minus any awarded result,
    -- which is decided off the pitch and never has one. Emitted beside games_with_team_stats, which
    -- this mart already exposes, because it is the denominator the gates below compare against and
    -- without it no test can tell a correct gate from one reverted to games_in_window.
    b.games_expecting_team_stats,
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
    -- every rate below is NULL ('—') unless each input it reads is present in every
    -- non-awarded leg of the window (engineering_standards.md section 3.2): the gate names the
    -- coverage count of each input, never a proxy for another column, and the guard
    -- assert_form_window_rates_inputs_covered fails the build where a gate is loose
    case
        when b.games_with_team_stats < b.games_expecting_team_stats then null
        else safe_divide(b.shots_total, b.games_with_team_stats)
    end as shots_per_match,
    case
        when b.games_with_sot_stats < b.games_expecting_team_stats then null
        when b.games_with_team_stats < b.games_expecting_team_stats then null
        else safe_divide(b.shots_on_goal, b.shots_total)
    end as shots_on_goal_pct,
    case
        when b.games_with_inside_box_stats < b.games_expecting_team_stats then null
        when b.games_with_team_stats < b.games_expecting_team_stats then null
        else safe_divide(b.shots_inside_box, b.shots_total)
    end as shots_inside_box_pct,
    case
        when b.games_with_sot_stats < b.games_expecting_team_stats then null
        else safe_divide(b.shots_on_goal, b.games_with_sot_stats) end
        as shots_on_goal_per_match,
    -- finishing efficiency: open-play conversion =
    -- (goals_for − goals_penalty − goals_own) / shots_on_goal. NULL ('—') unless the window is
    -- fully shot-covered AND the numerator is valid [0, shots_on_goal] — never a partial-window
    -- value and never >100% (penalties + own goals removed; a stray inconsistency nulls out).
    -- ⚠ SAME-WINDOW NUMERATOR, for the reason the season surface carries the identical note: the
    -- full goal sum includes an awarded result's goals, which have no shots behind them, against a
    -- denominator that can never count them. `goals_open_play_in_sot_games` restricts the numerator
    -- to the games the denominator covers.
    case
        when b.games_with_sot_stats < b.games_expecting_team_stats then null
        when b.goals_open_play_in_sot_games < 0 then null
        when b.goals_open_play_in_sot_games > b.shots_on_goal then null
        else safe_divide(b.goals_open_play_in_sot_games, b.shots_on_goal)
    end as finishing_efficiency_pct,
    case
        when b.games_with_passes_total_stats < b.games_expecting_team_stats then null
        else safe_divide(b.passes_total, b.games_with_passes_total_stats)
    end as passes_per_match,
    case
        when b.games_with_passes_accurate_stats < b.games_expecting_team_stats then null
        when b.games_with_passes_total_stats < b.games_expecting_team_stats then null
        else safe_divide(b.passes_accurate, b.passes_total)
    end as passes_accuracy_pct,
    case
        when b.games_with_corner_stats < b.games_expecting_team_stats then null
        else safe_divide(b.corner_kicks, b.games_with_corner_stats)
    end as corners_per_match,
    case
        when b.games_with_opp_stats < b.games_expecting_team_stats then null
        else safe_divide(b.opponent_corner_kicks, b.games_with_opp_stats) end
        as corners_against_per_match,
    -- goalkeeper: saves / (saves + goals conceded in save-covered games); self-bounded
    case
        when b.games_with_save_stats < b.games_expecting_team_stats then null
        else safe_divide(
            b.goalkeeper_saves, b.goalkeeper_saves + b.goals_against_in_save_games
        )
    end as saves_pct,
    -- player-derived team metrics: a leg without the player feed has no input, so these follow
    -- the same rule as the team-feed rates (docs/metric_layer.md)
    case
        when b.games_with_player_stats < b.games_expecting_team_stats then null
        else safe_divide(b.key_passes, b.games_with_player_stats)
    end as passes_key_per_match,
    case
        when b.games_with_player_stats < b.games_expecting_team_stats then null
        else safe_divide(b.tackles, b.games_with_player_stats)
    end as tackles_per_match,
    case
        when b.games_with_player_stats < b.games_expecting_team_stats then null
        else safe_divide(b.interceptions, b.games_with_player_stats)
    end as interceptions_per_match,
    case
        when b.games_with_player_stats < b.games_expecting_team_stats then null
        else safe_divide(b.blocks, b.games_with_player_stats)
    end as blocks_per_match,
    case
        when b.games_with_player_stats < b.games_expecting_team_stats then null
        else safe_divide(b.tackles + b.interceptions + b.blocks, b.games_with_player_stats)
    end as defensive_actions_per_match,
    case
        when b.games_with_player_stats < b.games_expecting_team_stats then null
        else safe_divide(b.duels_total, b.games_with_player_stats)
    end as duels_per_match,
    case
        when b.games_with_player_stats < b.games_expecting_team_stats then null
        else safe_divide(b.duels_won, b.duels_total)
    end as duels_won_pct
from builder as b
inner join fixtures as f
    on b.upcoming_fixture_sk = f.fixture_sk
