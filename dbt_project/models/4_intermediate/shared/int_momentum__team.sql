{{ config(materialized='table') }}

{#
  W1 momentum builder — team.

  Aggregates raw totals over the window legs selected by int_momentum_window__team
  (the selection was extracted there in #323 so this aggregate and the drill-down list
  mart consume the same matches). The window is last-5 for most competitions and
  cumulative (tournament_to_date / qualifiers) for tournament fixtures (GAP-18); the
  window_type carried from the selection says which, and games_in_window is the actual
  count (1–5 for last_5, unbounded for tournament windows). No ratios — those are
  computed in mart_momentum__team.

  Grain: (upcoming_fixture_sk, team_sk).

  Scope: all competition types — club and national. W1 is shown alongside W2 for every
  fixture; both numbers are always presented together.

  Returns no row when a team has no finished matches yet (before phase for a
  club domestic_league). The mart will emit nulls; #326 fills the gap.

  Player-derived columns (key_passes, tackles, …) inherit player-stat coverage
  gaps: if none of the window legs have player data the column is NULL; if some do,
  the sum covers only those matches. games_with_player_stats tracks coverage.

  Coverage rule (same-window): a ratio's numerator and denominator must cover the
  same games. Team stats (shots, passes, corners, saves) are sparse in lower
  leagues, so the builder carries per-input coverage counts and coverage-restricted
  scoreline sums; the mart divides each metric over the matching window. Where no
  covered game exists the mart yields NULL (we never divide a full-window numerator
  by a partial-window denominator).
#}

with window_legs as (
    select * from {{ ref('int_momentum_window__team') }}
),

-- Aggregate raw totals over the window legs
team_agg as (
    select
        upcoming_fixture_sk,
        team_sk,
        season_api_year,
        entity_type,
        window_type,
        count(*) as games_in_window,
        -- per-input coverage: stats are sparse in lower leagues, so each rate
        -- must divide over the games where its inputs actually exist
        countif(shots_total is not null) as games_with_team_stats,
        -- shots_on_goal can be null where shots_total isn't: the SoT rate needs
        -- its own coverage count (same-window rule)
        countif(shots_on_goal is not null) as games_with_sot_stats,
        countif(opponent_corner_kicks is not null) as games_with_opp_stats,
        -- save coverage: save_ratio is a team-feed (goalkeeper) metric, so it needs its own
        -- coverage count to NULL on partial coverage (universal incomplete-data rule)
        countif(goalkeeper_saves is not null) as games_with_save_stats,
        array_agg(distinct leg_league_code order by leg_league_code)
            as contributing_competitions,
        sum(case result when 'W' then 3 when 'D' then 1 else 0 end)
            as points_won,
        sum(goals_for) as goals_for,
        sum(goals_against) as goals_against,
        -- scoreline-based, full window (clean sheets display as x of games)
        countif(goals_against = 0) as clean_sheet_games,
        -- open-play goal components (CPO Option A): goals_open_play = goals_for − goals_penalty
        -- − goals_own (computed in the mart). Full-window sums — finishing is NULL unless the
        -- window is fully shot-covered (games_with_sot_stats = games_in_window), so there is no
        -- coverage-restricted goals sum to keep.
        sum(goals_penalty) as goals_penalty,
        sum(goals_own) as goals_own,
        -- coverage-restricted scoreline sum keeps save_ratio same-window with its denominator
        sum(if(goalkeeper_saves is not null, goals_against, null))
            as goals_against_in_save_games,
        sum(shots_total) as shots_total,
        sum(shots_on_goal) as shots_on_goal,
        sum(shots_inside_box) as shots_inside_box,
        sum(passes_total) as passes_total,
        sum(passes_accurate) as passes_accurate,
        sum(corner_kicks) as corner_kicks,
        sum(opponent_corner_kicks) as opponent_corner_kicks,
        sum(goalkeeper_saves) as goalkeeper_saves
    from window_legs
    group by
        upcoming_fixture_sk,
        team_sk,
        season_api_year,
        entity_type,
        window_type
),

-- Sum player-derived stats for the same window legs (inherits player-stat coverage gaps)
player_derived as (
    select
        wl.upcoming_fixture_sk,
        wl.team_sk,
        countif(p.fixture_sk is not null) as games_with_player_stats,
        sum(p.key_passes) as key_passes,
        sum(p.tackles) as tackles,
        sum(p.interceptions) as interceptions,
        sum(p.blocks) as blocks,
        sum(p.duels_total) as duels_total,
        sum(p.duels_won) as duels_won
    from window_legs as wl
    left join {{ ref('int_legs__team_from_players') }} as p
        on
            wl.leg_fixture_sk = p.fixture_sk
            and wl.team_sk = p.team_sk
    group by
        wl.upcoming_fixture_sk,
        wl.team_sk
)

select
    ta.upcoming_fixture_sk,
    ta.team_sk,
    ta.season_api_year,
    ta.entity_type,
    ta.window_type,
    ta.games_in_window,
    ta.games_with_team_stats,
    ta.games_with_sot_stats,
    ta.games_with_opp_stats,
    ta.games_with_save_stats,
    ta.contributing_competitions,
    ta.points_won,
    ta.goals_for,
    ta.goals_against,
    ta.clean_sheet_games,
    ta.goals_penalty,
    ta.goals_own,
    ta.goals_against_in_save_games,
    ta.shots_total,
    ta.shots_on_goal,
    ta.shots_inside_box,
    ta.passes_total,
    ta.passes_accurate,
    ta.corner_kicks,
    ta.opponent_corner_kicks,
    ta.goalkeeper_saves,
    pd.games_with_player_stats,
    pd.key_passes,
    pd.tackles,
    pd.interceptions,
    pd.blocks,
    pd.duels_total,
    pd.duels_won
from team_agg as ta
left join player_derived as pd
    on
        ta.upcoming_fixture_sk = pd.upcoming_fixture_sk
        and ta.team_sk = pd.team_sk
