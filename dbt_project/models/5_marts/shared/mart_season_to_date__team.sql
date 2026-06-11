{{ config(materialized='view') }}

{#
  W2 season-to-date mart — team. One row per upcoming fixture side: the team's cumulative
  record in the fixture's own competition this season (the number shown beside W1 momentum).

  Source: int_season_to_date__team (cumulative builder). For each upcoming fixture side we
  take the team's LATEST season-to-date row for the fixture's (league_code, season_api_year);
  if the team has not played in that competition this season yet (before phase), we fall
  back to the same competition's previous season final value (window_type = 'prev_season').

  Ratios computed here (same metric_ids and formulas as mart_momentum__team — the catalogue
  is window-agnostic). Same-window coverage rule from #320: per-match rates divide by the
  matching cumulative coverage count; finishing_efficiency / save_ratio use the
  coverage-restricted scoreline sums; null when no covered game.

  Grain: (upcoming_fixture_sk, team_sk).
#}

with upcoming as (
    select
        fixture_sk,
        home_team_sk,
        away_team_sk,
        league_code,
        season_api_year
    from {{ ref('fct_fixture') }}
    where
        status_short in ('NS', 'TBD')
        and fixture_date >= current_date()
),

sides as (
    select
        fixture_sk as upcoming_fixture_sk,
        home_team_sk as team_sk,
        league_code,
        season_api_year,
        true as is_home
    from upcoming

    union all

    select
        fixture_sk as upcoming_fixture_sk,
        away_team_sk as team_sk,
        league_code,
        season_api_year,
        false as is_home
    from upcoming
),

-- The season-final cumulative row per (team, competition, season) = totals through the
-- team's latest played match that season.
season_final as (
    select *
    from {{ ref('int_season_to_date__team') }}
    qualify row_number() over (
        partition by team_sk, league_code, season_api_year
        order by kickoff_datetime desc, fixture_sk desc
    ) = 1
),

-- Current season if the team has played; else previous season of the same competition.
matched as (
    select
        s.upcoming_fixture_sk,
        s.team_sk,
        s.league_code,
        s.is_home,
        sf.entity_type,
        sf.season_api_year,
        'season_to_date' as window_type,
        sf.games_played,
        sf.games_with_team_stats,
        sf.games_with_opp_stats,
        sf.games_with_player_stats,
        sf.points_won,
        sf.wins,
        sf.draws,
        sf.losses,
        sf.clean_sheet_games,
        sf.goals_for,
        sf.goals_against,
        sf.goals_for_in_shot_games,
        sf.goals_against_in_save_games,
        sf.shots_total,
        sf.shots_on_goal,
        sf.shots_inside_box,
        sf.passes_total,
        sf.passes_accurate,
        sf.corner_kicks,
        sf.opponent_corner_kicks,
        sf.goalkeeper_saves,
        sf.key_passes,
        sf.tackles,
        sf.interceptions,
        sf.blocks,
        sf.duels_total,
        sf.duels_won,
        sf.dribbles_attempts,
        sf.dribbles_success,
        1 as priority
    from sides as s
    inner join season_final as sf
        on
            s.team_sk = sf.team_sk
            and s.league_code = sf.league_code
            and s.season_api_year = sf.season_api_year

    union all

    select
        s.upcoming_fixture_sk,
        s.team_sk,
        s.league_code,
        s.is_home,
        sf.entity_type,
        sf.season_api_year,
        'prev_season' as window_type,
        sf.games_played,
        sf.games_with_team_stats,
        sf.games_with_opp_stats,
        sf.games_with_player_stats,
        sf.points_won,
        sf.wins,
        sf.draws,
        sf.losses,
        sf.clean_sheet_games,
        sf.goals_for,
        sf.goals_against,
        sf.goals_for_in_shot_games,
        sf.goals_against_in_save_games,
        sf.shots_total,
        sf.shots_on_goal,
        sf.shots_inside_box,
        sf.passes_total,
        sf.passes_accurate,
        sf.corner_kicks,
        sf.opponent_corner_kicks,
        sf.goalkeeper_saves,
        sf.key_passes,
        sf.tackles,
        sf.interceptions,
        sf.blocks,
        sf.duels_total,
        sf.duels_won,
        sf.dribbles_attempts,
        sf.dribbles_success,
        2 as priority
    from sides as s
    inner join season_final as sf
        on
            s.team_sk = sf.team_sk
            and s.league_code = sf.league_code
            and sf.season_api_year = s.season_api_year - 1
),

chosen as (
    select *
    from matched
    qualify row_number() over (
        partition by upcoming_fixture_sk, team_sk
        order by priority asc
    ) = 1
)

select
    upcoming_fixture_sk,
    team_sk,
    league_code,
    entity_type,
    season_api_year,
    window_type,
    games_played,
    games_with_team_stats,
    is_home,
    points_won,
    -- W/D/L counts (the W2 form display — pills misrepresent a season window)
    wins,
    draws,
    losses,
    -- clean sheets: scoreline-based count, displays as x of games_played
    clean_sheet_games as clean_sheets,
    -- goals (scoreline window)
    safe_divide(goals_for, games_played) as goals_per_match,
    safe_divide(goals_against, games_played) as goals_against_per_match,
    -- shots (team-stat window)
    safe_divide(shots_total, games_with_team_stats) as shots_per_match,
    safe_divide(shots_on_goal, shots_total) as shot_accuracy,
    safe_divide(shots_inside_box, shots_total) as danger_zone_ratio,
    safe_divide(shots_on_goal, games_with_team_stats) as shots_on_target_per_match,
    safe_divide(goals_for_in_shot_games, shots_on_goal) as finishing_efficiency,
    -- passing (team-stat window)
    safe_divide(passes_total, games_with_team_stats) as passes_per_match,
    safe_divide(passes_accurate, passes_total) as pass_accuracy,
    -- set pieces
    safe_divide(corner_kicks, games_with_team_stats) as corner_kicks_per_match,
    safe_divide(opponent_corner_kicks, games_with_opp_stats)
        as corners_conceded_per_match,
    -- goalkeeper: self-bounding (saves / (saves + goals conceded in save-covered games))
    safe_divide(goalkeeper_saves, goalkeeper_saves + goals_against_in_save_games)
        as save_ratio,
    -- player-derived team metrics (player-stat window; null when unavailable)
    safe_divide(key_passes, games_with_player_stats) as key_passes_per_match,
    safe_divide(tackles, games_with_player_stats) as tackles_per_match,
    safe_divide(interceptions, games_with_player_stats) as interceptions_per_match,
    safe_divide(blocks, games_with_player_stats) as blocks_per_match,
    -- T+I+B share one coverage window (same player rows): same-window by construction
    safe_divide(tackles + interceptions + blocks, games_with_player_stats)
        as defensive_actions_per_match,
    safe_divide(duels_total, games_with_player_stats) as duels_per_match,
    safe_divide(duels_won, duels_total) as duels_won_pct,
    safe_divide(dribbles_success, dribbles_attempts) as dribbles_success_pct
from chosen
