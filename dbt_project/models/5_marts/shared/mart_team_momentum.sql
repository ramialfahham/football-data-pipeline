{#
  W1 momentum mart — team.

  The displayed form-window metrics, taken from int_team_momentum__metrics, where they are the
  catalogue formulas over the window's legs. The window is last-5 for most competitions and
  cumulative for tournament fixtures (window_type, GAP-18). Nothing is computed here.

  Grain: (upcoming_fixture_sk, team_sk).

  league_rank is not computed here — it comes from the standings surface (#322).
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
    -- which is decided off the pitch and never has one
    b.games_expecting_team_stats,
    b.games_with_team_stats,
    b.contributing_competitions,
    b.games_with_player_stats,
    b.points_won,
    -- clean sheets: displays as x of games_expecting_team_stats
    b.clean_sheets,
    b.goals_per_match,
    b.goals_against_per_match,
    b.shots_per_match,
    b.shots_on_goal_pct,
    b.shots_inside_box_pct,
    b.shots_on_goal_per_match,
    b.finishing_efficiency_pct,
    b.passes_per_match,
    b.passes_accuracy_pct,
    b.corners_per_match,
    b.corners_against_per_match,
    b.saves_pct,
    b.passes_key_per_match,
    b.tackles_per_match,
    b.interceptions_per_match,
    b.blocks_per_match,
    b.defensive_actions_per_match,
    b.duels_per_match,
    b.duels_won_pct,
    b.team_sk = f.home_team_sk as is_home
from builder as b
inner join fixtures as f
    on b.upcoming_fixture_sk = f.fixture_sk
