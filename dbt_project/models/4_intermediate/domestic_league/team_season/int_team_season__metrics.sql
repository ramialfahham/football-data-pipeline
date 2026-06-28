{{ config(materialized='table') }}

{#
  Whole-season team rollup — the FINAL ROW of int_team_season_record (#500 PR1: one season
  aggregation, not two). Per (league_code, season_api_year, team_sk) over all finished legs in the
  season — identical numbers to the prior independent re-aggregation, now a projection of the
  cumulative season-to-date model rather than a second pass over the legs.
  Grain: (team_sk, season_sk). mart_team_season_insights keeps latest season per league.

  The shared per-match / ratio formulas are plain inline SQL below — the same window-form as
  mart_team_momentum / mart_team_season_record (the latter COMPOSES this model, never re-derives).
  The metric columns now match the catalogue ids — the `_season` suffix was dropped end-to-end in
  #500 Stage 2 (the live team_season_insights.json keys moved in lockstep). Window-specific season metrics
  (points_capture, shot_share, clean-sheets RATE) stay inline — they are not shared across windows.

  Incomplete-data → NULL (CPO 2026-06-25; reverse #320) is enforced inline (a team-feed rate is
  NULL unless its stat covers every season game); scoreline + player-derived are not gated.
#}

with season_final as (
    -- the last cumulative row per (team, competition, season) = the whole-season totals
    select * from {{ ref('int_team_season_record') }}
    qualify row_number() over (
        partition by team_sk, league_code, season_api_year
        order by kickoff_datetime desc, fixture_sk desc
    ) = 1
),

matchdays as (
    -- distinct matchdays used (round_name lives on the leg, not the cumulative row)
    select
        team_sk,
        league_code,
        season_api_year,
        count(distinct round_name) as season_matchdays_used
    from {{ ref('int_legs__team_match') }}
    group by team_sk, league_code, season_api_year
),

final as (
    select
        sf.*,
        md.season_matchdays_used
    from season_final as sf
    left join matchdays as md
        on
            sf.team_sk = md.team_sk
            and sf.league_code = md.league_code
            and sf.season_api_year = md.season_api_year
)

select
    {{ dbt_utils.generate_surrogate_key(['team_sk', 'season_sk']) }} as team_season_sk,
    team_sk,
    league_sk,
    season_sk,
    league_code,
    season_api_year,
    entity_type,
    games_played as season_games_played,
    season_matchdays_used,
    games_with_sot_stats as stat_coverage_season_games,
    games_with_player_stats as player_stat_coverage_season_games,
    games_with_team_stats,
    -- raw season-total counts (kept under the _sum_season names — live JSON keys; the metric columns
    -- dropped their _season suffix in #500 Stage 2, but these raw sums keep the window marker)
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
    -- team-feed sum columns: NULL ('—') on partial coverage (incomplete-data rule, CPO 2026-06-25).
    -- These are the DISPLAYED season totals; the per-match rates below gate independently off the
    -- raw cumulative columns. Scoreline sums above are always present, so they are NOT gated.
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
    -- window-specific season metrics (not shared across windows; stay inline)
    safe_divide(points_won, 3 * games_played) as points_capture,
    -- shot share: NULL unless BOTH own and opponent shots cover every game (else a partial value)
    case
        when games_with_team_stats < games_played then null
        when games_with_opp_stats < games_played then null
        else safe_divide(shots_total, nullif(shots_total + opponent_shots_total, 0))
    end as shot_share,
    safe_divide(clean_sheet_games, games_played) as clean_sheets,
    -- shared per-match / ratio formulas (plain inline SQL — same window-form as the marts; the
    -- metric columns match the catalogue ids since #500 Stage 2). Composed (not recomputed)
    -- by mart_team_season_record.
    safe_divide(goals_for, games_played) as goals_per_match,
    safe_divide(goals_against, games_played) as goals_against_per_match,
    case
        when games_with_team_stats < games_played then null
        else safe_divide(shots_total, games_with_team_stats)
    end as shots_per_match,
    case
        -- gate on BOTH SoT (numerator) and team (denominator) coverage: in rare old data a game
        -- carries shots_on_goal but null shots_total, so SoT coverage alone is not sufficient.
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
    -- shots-on-target conceded per match: opponent-SoT companion to shots_on_goal_per_match;
    -- NULL unless opponent SoT covers every game (incomplete-data rule, CPO 2026-06-25).
    case
        when games_with_opp_sot_stats < games_played then null
        else safe_divide(opponent_shots_on_goal, games_with_opp_sot_stats)
    end as shots_on_goal_against_per_match,
    -- sot_difference (deserved signal): per-match shots-on-target difference (for - against). The
    -- catalogue denominator is count(*) = matches; this APPLIES it only when BOTH own and opponent
    -- SoT cover every game (availability gate — never part of the formula). Signed: can be negative.
    case
        when games_with_sot_stats < games_played then null
        when games_with_opp_sot_stats < games_played then null
        else safe_divide(shots_on_goal - opponent_shots_on_goal, games_played)
    end as sot_difference,
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
    -- save_ratio: byte-identical to the prior model (which divided by goals_against TOTAL) — the
    -- gate makes BOTH null on partial save coverage, and when fully covered every game is
    -- save-covered so goals_against_in_save_games == goals_against (verified 0/12537).
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
from final
