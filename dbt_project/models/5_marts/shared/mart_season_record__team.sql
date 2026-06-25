{{ config(materialized='view') }}

{#
  W2 season-record mart — team. One row per upcoming fixture side: the team's cumulative
  record in the fixture's own competition this season (the number shown beside W1 momentum).

  Source: int_season_record__team (cumulative builder). For each upcoming fixture side we
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
    from {{ ref('int_season_record__team') }}
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
        sf.games_with_sot_stats,
        sf.games_with_opp_stats,
        sf.games_with_save_stats,
        sf.games_with_player_stats,
        sf.points_won,
        sf.wins,
        sf.draws,
        sf.losses,
        sf.clean_sheet_games,
        sf.goals_for,
        sf.goals_against,
        sf.goals_penalty,
        sf.goals_own,
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
        sf.games_with_sot_stats,
        sf.games_with_opp_stats,
        sf.games_with_save_stats,
        sf.games_with_player_stats,
        sf.points_won,
        sf.wins,
        sf.draws,
        sf.losses,
        sf.clean_sheet_games,
        sf.goals_for,
        sf.goals_against,
        sf.goals_penalty,
        sf.goals_own,
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
    -- shots (team-stat window): NULL ('—') on partial coverage — never a partial-window average
    -- (reverse #320; universal incomplete-data rule, CPO 2026-06-25). shot_accuracy / danger_zone
    -- gate on the binding shot coverage (SoT ⊆ team-stat, so full SoT coverage ⇒ full shots_total).
    case
        when games_with_team_stats < games_played then null
        else safe_divide(shots_total, games_with_team_stats)
    end as shots_per_match,
    case
        when games_with_sot_stats < games_played then null
        else safe_divide(shots_on_goal, shots_total)
    end as shot_accuracy,
    case
        when games_with_team_stats < games_played then null
        else safe_divide(shots_inside_box, shots_total)
    end as danger_zone_ratio,
    case
        when games_with_sot_stats < games_played then null
        else safe_divide(shots_on_goal, games_with_sot_stats)
    end as shots_on_goal_per_match,
    -- finishing efficiency (CPO Option A): open-play conversion =
    -- (goals_for − goals_penalty − goals_own) / shots_on_goal. NULL ('—') unless fully
    -- shot-covered AND the numerator is valid [0, shots_on_goal] — never partial, never >100%.
    case
        when games_with_sot_stats < games_played then null
        when (goals_for - goals_penalty - goals_own) < 0 then null
        when (goals_for - goals_penalty - goals_own) > shots_on_goal then null
        else safe_divide(goals_for - goals_penalty - goals_own, shots_on_goal)
    end as finishing_efficiency,
    -- passing (team-stat window): NULL on partial coverage
    case
        when games_with_team_stats < games_played then null
        else safe_divide(passes_total, games_with_team_stats)
    end as passes_per_match,
    case
        when games_with_team_stats < games_played then null
        else safe_divide(passes_accurate, passes_total)
    end as pass_accuracy,
    -- set pieces (conceded uses opponent-stat coverage): NULL on partial coverage
    case
        when games_with_team_stats < games_played then null
        else safe_divide(corner_kicks, games_with_team_stats)
    end as corner_kicks_per_match,
    case
        when games_with_opp_stats < games_played then null
        else safe_divide(opponent_corner_kicks, games_with_opp_stats) end
        as corners_conceded_per_match,
    -- goalkeeper: self-bounding (saves / (saves + goals conceded in save-covered games)).
    -- NULL on partial save coverage (the new games_with_save_stats).
    case
        when games_with_save_stats < games_played then null
        else safe_divide(goalkeeper_saves, goalkeeper_saves + goals_against_in_save_games)
    end as save_ratio,
    -- player-derived team metrics: DELIBERATELY left on average-over-player-covered games (NOT
    -- gated) — these are player data, and missing player stats must not blank a team stat
    -- (CPO 2026-06-25). null only when no player-covered game exists (safe_divide by 0).
    safe_divide(key_passes, games_with_player_stats) as key_passes_per_match,
    safe_divide(tackles, games_with_player_stats) as tackles_per_match,
    safe_divide(interceptions, games_with_player_stats) as interceptions_per_match,
    safe_divide(blocks, games_with_player_stats) as blocks_per_match,
    -- T+I+B share one coverage window (same player rows): same-window by construction
    safe_divide(tackles + interceptions + blocks, games_with_player_stats)
        as defensive_actions_per_match,
    safe_divide(duels_total, games_with_player_stats) as duels_per_match,
    safe_divide(duels_won, duels_total) as duels_won_pct
from chosen
