{{ config(materialized='table') }}

{#
  Team profile (#324). One row per (team, competition-season): the full profile
  surface a team page renders. Composes existing season rollups and adds the two
  signature differentiators plus a lighter streaks layer.

  Table stakes (composed, not recomputed):
    - identity            dim_team
    - record / rank / form  mart_team_season (same-layer ref, the documented
                            layering exception — mart_team_season_insights does
                            the same)
    - season metric rates  int_team_season__full_season_metrics

  Differentiators:
    - Deserved vs actual — shot_share_season + danger_zone_ratio_season (chance
      dominance) shown against points_capture_season + latest_rank (actual
      achievement), with a transparent performance_vs_results_gap. Two real
      ratios and their difference, NOT a fabricated composite score.
    - Vs own history — matchday-aligned year-over-year (this season vs last,
      through the same matchday), domestic leagues only, from
      int_team_profile__yoy. NULL for non-domestic competitions and where the
      prior season is not ingested (history_seasons = 1).
    - Streaks (lighter layer) — trailing unbeaten / win / winless / clean-sheet /
      scoring runs from int_team_profile__streaks.

  Grain: (team_sk, season_sk).
#}

with metrics as (
    select * from {{ ref('int_team_season__full_season_metrics') }}
),

team_season as (
    select * from {{ ref('mart_team_season') }}
),

teams as (
    select * from {{ ref('dim_team') }}
),

registry as (
    select
        league_code,
        competition_type
    from {{ ref('competition_registry') }}
),

yoy as (
    select * from {{ ref('int_team_profile__yoy') }}
),

streaks as (
    select * from {{ ref('int_team_profile__streaks') }}
)

select
    m.team_sk,
    m.season_sk,
    m.league_sk,
    m.league_code,
    m.season_api_year,
    reg.competition_type,
    -- identity
    t.team_name,
    t.team_code,
    t.team_country,
    t.team_logo_url,
    -- record / rank / form
    ts.played,
    ts.wins,
    ts.draws,
    ts.losses,
    ts.goals_for,
    ts.goals_against,
    ts.goal_diff,
    ts.points,
    ts.clean_sheets,
    ts.latest_rank,
    ts.latest_form,
    -- season metric rates
    m.season_games_played,
    m.stat_coverage_season_games,
    m.goals_per_match_season,
    m.goals_against_per_match_season,
    m.shots_per_match_season,
    m.shot_accuracy_season,
    m.danger_zone_ratio_season,
    m.finishing_efficiency_season,
    m.pass_accuracy_season,
    m.passes_per_match_season,
    m.corner_kicks_per_match_season,
    m.corners_conceded_per_match_season,
    m.save_ratio_season,
    -- GAP-13: locked-contract season variants (player-derived ones inherit
    -- player-stat coverage gaps; caption from player_stat_coverage_season_games)
    m.player_stat_coverage_season_games,
    m.shots_on_target_per_match_season,
    m.key_passes_per_match_season,
    m.duels_per_match_season,
    m.duels_won_pct_season,
    m.defensive_actions_per_match_season,
    -- deserved vs actual: dominance (shot_share) vs achievement (points_capture)
    m.shot_share_season,
    m.points_capture_season,
    -- year-over-year (domestic only; NULL otherwise / when prior season absent)
    y.yoy_games_played_cutoff,
    y.points_this_season,
    y.points_prev_season,
    y.points_delta_yoy,
    y.goals_for_this_season,
    y.goals_for_prev_season,
    y.goals_for_delta_yoy,
    y.goals_against_this_season,
    y.goals_against_prev_season,
    y.goals_against_delta_yoy,
    -- streaks (trailing run as of the latest match)
    s.unbeaten_run,
    s.win_run,
    s.winless_run,
    s.clean_sheet_run,
    s.scoring_run,
    -- transparent over/under-performance signal (positive = dominates play more
    -- than results reward; both inputs are real [0,1] shares, no composite score)
    m.shot_share_season - m.points_capture_season as performance_vs_results_gap
from metrics as m
left join team_season as ts
    on m.team_season_sk = ts.team_season_sk
left join teams as t
    on m.team_sk = t.team_sk
left join registry as reg
    on m.league_code = reg.league_code
left join yoy as y
    on
        m.team_sk = y.team_sk
        and m.league_code = y.league_code
        and m.season_api_year = y.season_api_year
left join streaks as s
    on
        m.team_sk = s.team_sk
        and m.season_sk = s.season_sk
