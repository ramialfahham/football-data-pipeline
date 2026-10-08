{#
  W1 momentum mart — team.

  The displayed form-window metrics, taken from int_team_momentum__metrics, where they are the
  catalogue formulas over the window that window_type names. Nothing is computed here.

  Grain: (upcoming_fixture_sk, team_sk).

  league_rank is not computed here — it comes from the standings surface (#322).
  is_form_window is false only before the team's first match in a domestic league this season, when
  docs/metrics_context_model.md §4 shows last season's record in that league instead.
#}

with builder as (
    select * from {{ ref('int_team_momentum__metrics') }}
),

fixtures as (
    select
        fixture_sk,
        league_code,
        season_api_year,
        home_team_sk
    from {{ ref('fct_fixture') }}
),

domestic_leagues as (
    select league_code
    from {{ ref('competition_registry') }}
    where competition_type = 'domestic_league'
),

played_this_season as (
    select distinct
        team_sk,
        league_code,
        season_api_year
    from {{ ref('int_team_season__metrics') }}
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
    b.shots_on_goal_against_per_match,
    b.shots_off_target_per_match,
    b.shots_blocked_per_match,
    b.shots_inside_box_per_match,
    b.passes_accurate_per_match,
    b.passes_share_pct,
    b.dribbles_attempts_per_match,
    b.dribbles_success_per_match,
    b.dribbles_success_pct,
    b.duels_won_per_match,
    b.saves_per_match,
    b.free_kicks_per_match,
    b.fouls_per_match,
    b.offsides_per_match,
    b.cards_yellow_per_match,
    b.cards_red_per_match,
    b.team_sk = f.home_team_sk as is_home,
    p.team_sk is not null or f.league_code not in (select d.league_code from domestic_leagues as d) as is_form_window
from builder as b
inner join fixtures as f
    on b.upcoming_fixture_sk = f.fixture_sk
left join played_this_season as p
    on b.team_sk = p.team_sk and f.league_code = p.league_code and f.season_api_year = p.season_api_year
