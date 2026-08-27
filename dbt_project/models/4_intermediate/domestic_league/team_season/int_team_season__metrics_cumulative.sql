{{ config(materialized='table') }}

{#
  Per-matchday cumulative team-season metrics — the season rate formulas applied to EVERY
  cumulative row of int_team_season_record (not just the final one). This is the single home of
  the team-season rate formulas (#500 one-aggregation philosophy):

    - int_team_season__metrics is the FINAL-ROW PROJECTION of this model (whole-season rollup) —
      byte-identical output, so every downstream consumer (mart_team_season / _insights /
      _profile / _record, the benchmark chain, deserved-vs-actual) is unchanged.
    - int_team_profile__yoy COMPOSES this model at the games-played cutoff N to align two seasons
      by matchday for ALL metrics ("this season through N vs last season through its first N").
      int_team_season_record's header keeps match_number for exactly this.

  Grain: (team_sk, league_code, season_api_year, match_number). All-competitions, like
  int_team_season__metrics (no domestic filter — the YoY consumer applies that).

  NAMING NOTE: the `_sum_season` / `season_games_played` / `stat_coverage_season_games` column
  names are inherited verbatim from the whole-season projection so the projection is a trivial
  final-row select (guaranteeing byte-identity). HERE they mean "cumulative THROUGH THIS matchday",
  not the whole season. Formulas + coverage gates are lifted verbatim from int_team_season__metrics.

  Incomplete-data → NULL (CPO 2026-06-25): a team-feed rate is NULL unless its stat covers every
  game through this matchday (games_with_* == games_played); scoreline + player-derived are not gated.
#}

with rec as (
    select * from {{ ref('int_team_season_record') }}
)

select
    team_sk,
    league_sk,
    season_sk,
    league_code,
    season_api_year,
    entity_type,
    -- the matchday cutoff key (this model's grain; the YoY alignment key). games_played is the
    -- same value carried under the season name below for the byte-identical projection.
    match_number,
    games_played as season_games_played,
    games_with_sot_stats as stat_coverage_season_games,
    games_with_player_stats as player_stat_coverage_season_games,
    games_with_team_stats,
    -- raw cumulative counts (kept under the _sum_season names — the projection's live JSON keys)
    points_won as points_won_sum_season,
    wins as wins_sum_season,
    draws as draws_sum_season,
    losses as losses_sum_season,
    clean_sheet_games as clean_sheets_sum_season,
    goals_for as goals_for_sum_season,
    goals_against as goals_against_sum_season,
    goals_penalty,
    goals_own,
    goals_for - goals_penalty - goals_own as goals_open_play,
    -- team-feed sum columns: NULL ('—') on partial coverage through this matchday.
    case
        when games_with_team_stats < games_played then null else shots_total
    end as total_shots_sum_season,
    case
        when games_with_opp_stats < games_played then null else opponent_shots_total
    end as opponent_total_shots_sum_season,
    case
        when games_with_team_stats < games_played then null else shots_inside_box
    end as shots_inside_box_sum_season,
    case
        when games_with_sot_stats < games_played then null else shots_on_goal
    end as shots_on_goal_sum_season,
    case
        when games_with_team_stats < games_played then null else corner_kicks
    end as corner_kicks_sum_season,
    case
        when games_with_opp_stats < games_played then null else opponent_corner_kicks
    end as opponent_corner_kicks_sum_season,
    case
        when games_with_team_stats < games_played then null else passes_accurate
    end as passes_accurate_sum_season,
    case
        when games_with_team_stats < games_played then null else passes_total
    end as passes_total_sum_season,
    case
        when games_with_save_stats < games_played then null else goalkeeper_saves
    end as goalkeeper_saves_sum_season,
    -- window-specific metrics (stay inline; same as the whole-season model)
    safe_divide(points_won, 3 * games_played) as points_capture_pct,
    case
        when games_with_team_stats < games_played then null
        when games_with_opp_stats < games_played then null
        else safe_divide(shots_total, nullif(shots_total + opponent_shots_total, 0))
    end as shot_share,
    safe_divide(clean_sheet_games, games_played) as clean_sheets_pct,
    -- shared per-match / ratio formulas (plain inline SQL; catalogue-id names). Lifted verbatim
    -- from int_team_season__metrics — this model is now their single home.
    safe_divide(goals_for, games_played) as goals_per_match,
    safe_divide(goals_against, games_played) as goals_against_per_match,
    case
        when games_with_team_stats < games_played then null
        else safe_divide(shots_total, games_with_team_stats)
    end as shots_per_match,
    case
        when games_with_sot_stats < games_played then null
        when games_with_team_stats < games_played then null
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
    case
        when games_with_opp_sot_stats < games_played then null
        else safe_divide(opponent_shots_on_goal, games_with_opp_sot_stats)
    end as shots_on_goal_against_per_match,
    case
        when games_with_sot_stats < games_played then null
        when games_with_opp_sot_stats < games_played then null
        else safe_divide(shots_on_goal - opponent_shots_on_goal, games_played)
    end as sot_difference_per_match,
    case
        when games_with_sot_stats < games_played then null
        when (goals_for - goals_penalty - goals_own) < 0 then null
        when (goals_for - goals_penalty - goals_own) > shots_on_goal then null
        else safe_divide(goals_for - goals_penalty - goals_own, shots_on_goal)
    end as finishing_efficiency,
    case
        when games_with_team_stats < games_played then null
        else safe_divide(passes_total, games_with_team_stats)
    end as passes_per_match,
    case
        when games_with_team_stats < games_played then null
        else safe_divide(passes_accurate, passes_total)
    end as pass_accuracy,
    case
        when games_with_team_stats < games_played then null
        else safe_divide(corner_kicks, games_with_team_stats)
    end as corner_kicks_per_match,
    case
        when games_with_opp_stats < games_played then null
        else safe_divide(opponent_corner_kicks, games_with_opp_stats)
    end as corners_against_per_match,
    case
        when games_with_save_stats < games_played then null
        else safe_divide(
            goalkeeper_saves, goalkeeper_saves + goals_against_in_save_games
        )
    end as save_ratio,
    safe_divide(key_passes, games_with_player_stats) as key_passes_per_match,
    safe_divide(tackles, games_with_player_stats) as tackles_per_match,
    safe_divide(interceptions, games_with_player_stats)
        as interceptions_per_match,
    safe_divide(blocks, games_with_player_stats) as blocks_per_match,
    safe_divide(tackles + interceptions + blocks, games_with_player_stats)
        as defensive_actions_per_match,
    safe_divide(duels_total, games_with_player_stats) as duels_per_match,
    safe_divide(duels_won, duels_total) as duels_won_pct
from rec
