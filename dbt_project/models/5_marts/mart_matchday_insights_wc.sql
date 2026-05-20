{{ config(materialized='view') }}

{#
  FIFA World Cup (WC) matchday preview mart: same consumer column contract as
  mart_matchday_insights. Form logic is sourced from int_wc__matchday_team_form_metrics:
  - Group Stage round 1: supporting qualifier leagues
  - Group Stage round 2+ and knockout: cumulative WC tournament legs
#}

with import_int_matchday__upcoming_round_fixtures as (
    select * from {{ ref('int_matchday__upcoming_round_fixtures') }}
    where
        league_code = 'WC'
        and status_short = 'NS'
        and home_team_sk is not null
        and away_team_sk is not null
),

import_int_wc__matchday_team_form_metrics as (
    select * from {{ ref('int_wc__matchday_team_form_metrics') }}
),

mart_team_season as (
    select * from {{ ref('mart_team_season') }}
),

dim_team as (
    select * from {{ ref('dim_team') }}
),

home_form_matchday as (
    select
        fixture_sk,
        team_sk as home_team_sk,
        form_season_api_year,
        is_tournament_form,
        form_games_played,
        form_matchdays_used,
        stat_coverage_form_games,
        points_won_sum_form,
        goals_for_sum_form,
        goals_against_sum_form,
        total_shots_sum_form,
        opponent_total_shots_sum_form,
        shots_inside_box_sum_form,
        shots_on_goal_sum_form,
        corner_kicks_sum_form,
        opponent_corner_kicks_sum_form,
        passes_accurate_sum_form,
        passes_total_sum_form,
        goalkeeper_saves_sum_form,
        points_capture_recent,
        goals_per_match_recent,
        goals_against_per_match_recent,
        shots_per_match_recent,
        shot_share_recent,
        danger_zone_ratio_recent,
        shot_accuracy_recent,
        finishing_efficiency_recent,
        pass_accuracy_recent,
        passes_per_match_recent,
        corner_kicks_per_match_recent,
        corners_conceded_per_match_recent,
        save_ratio_recent
    from import_int_wc__matchday_team_form_metrics
),

away_form_matchday as (
    select
        fixture_sk,
        team_sk as away_team_sk,
        form_season_api_year,
        is_tournament_form,
        form_games_played,
        form_matchdays_used,
        stat_coverage_form_games,
        points_won_sum_form,
        goals_for_sum_form,
        goals_against_sum_form,
        total_shots_sum_form,
        opponent_total_shots_sum_form,
        shots_inside_box_sum_form,
        shots_on_goal_sum_form,
        corner_kicks_sum_form,
        opponent_corner_kicks_sum_form,
        passes_accurate_sum_form,
        passes_total_sum_form,
        goalkeeper_saves_sum_form,
        points_capture_recent,
        goals_per_match_recent,
        goals_against_per_match_recent,
        shots_per_match_recent,
        shot_share_recent,
        danger_zone_ratio_recent,
        shot_accuracy_recent,
        finishing_efficiency_recent,
        pass_accuracy_recent,
        passes_per_match_recent,
        corner_kicks_per_match_recent,
        corners_conceded_per_match_recent,
        save_ratio_recent
    from import_int_wc__matchday_team_form_metrics
),

final as (
    select
        um.fixture_sk,
        um.fixture_api_id,
        um.league_sk,
        um.season_sk,
        um.league_code,
        um.season_api_year,
        um.fixture_date,
        um.kickoff_datetime,
        um.round_name,
        um.upcoming_round_order,
        um.home_team_sk,
        um.home_team_name,
        um.away_team_sk,
        um.away_team_name,
        um.upcoming_matchday_fixture_count,
        um.league_name,
        home_ts.latest_rank as home_league_rank,
        away_ts.latest_rank as away_league_rank,
        home_ts.standings_group_description as home_standings_group_description,
        away_ts.standings_group_description as away_standings_group_description,
        home_dt.team_logo_url as home_team_logo_url,
        away_dt.team_logo_url as away_team_logo_url,

        hfm.form_season_api_year as home_form_season_api_year,
        hfm.form_games_played as home_form_games_played,
        hfm.form_matchdays_used as home_form_matchdays_used,
        hfm.stat_coverage_form_games as home_stat_coverage_form_games,
        hfm.points_won_sum_form as home_points_won_sum_form,
        hfm.goals_for_sum_form as home_goals_for_sum_form,
        hfm.goals_against_sum_form as home_goals_against_sum_form,
        hfm.total_shots_sum_form as home_total_shots_sum_form,
        hfm.opponent_total_shots_sum_form as home_opponent_total_shots_sum_form,
        hfm.shots_inside_box_sum_form as home_shots_inside_box_sum_form,
        hfm.shots_on_goal_sum_form as home_shots_on_goal_sum_form,
        hfm.corner_kicks_sum_form as home_corner_kicks_sum_form,
        hfm.opponent_corner_kicks_sum_form as home_opponent_corner_kicks_sum_form,
        hfm.passes_accurate_sum_form as home_passes_accurate_sum_form,
        hfm.passes_total_sum_form as home_passes_total_sum_form,
        hfm.goalkeeper_saves_sum_form as home_goalkeeper_saves_sum_form,
        hfm.points_capture_recent as home_points_capture_recent,
        hfm.goals_per_match_recent as home_goals_per_match_recent,
        hfm.goals_against_per_match_recent as home_goals_against_per_match_recent,
        hfm.shots_per_match_recent as home_shots_per_match_recent,
        hfm.shot_share_recent as home_shot_share_recent,
        hfm.danger_zone_ratio_recent as home_danger_zone_ratio_recent,
        hfm.shot_accuracy_recent as home_shot_accuracy_recent,
        hfm.finishing_efficiency_recent as home_finishing_efficiency_recent,
        hfm.pass_accuracy_recent as home_pass_accuracy_recent,
        hfm.passes_per_match_recent as home_passes_per_match_recent,
        hfm.corner_kicks_per_match_recent as home_corner_kicks_per_match_recent,
        hfm.corners_conceded_per_match_recent as home_corners_conceded_per_match_recent,
        hfm.save_ratio_recent as home_save_ratio_recent,

        afm.form_season_api_year as away_form_season_api_year,
        afm.form_games_played as away_form_games_played,
        afm.form_matchdays_used as away_form_matchdays_used,
        afm.stat_coverage_form_games as away_stat_coverage_form_games,
        afm.points_won_sum_form as away_points_won_sum_form,
        afm.goals_for_sum_form as away_goals_for_sum_form,
        afm.goals_against_sum_form as away_goals_against_sum_form,
        afm.total_shots_sum_form as away_total_shots_sum_form,
        afm.opponent_total_shots_sum_form as away_opponent_total_shots_sum_form,
        afm.shots_inside_box_sum_form as away_shots_inside_box_sum_form,
        afm.shots_on_goal_sum_form as away_shots_on_goal_sum_form,
        afm.corner_kicks_sum_form as away_corner_kicks_sum_form,
        afm.opponent_corner_kicks_sum_form as away_opponent_corner_kicks_sum_form,
        afm.passes_accurate_sum_form as away_passes_accurate_sum_form,
        afm.passes_total_sum_form as away_passes_total_sum_form,
        afm.goalkeeper_saves_sum_form as away_goalkeeper_saves_sum_form,
        afm.points_capture_recent as away_points_capture_recent,
        afm.goals_per_match_recent as away_goals_per_match_recent,
        afm.goals_against_per_match_recent as away_goals_against_per_match_recent,
        afm.shots_per_match_recent as away_shots_per_match_recent,
        afm.shot_share_recent as away_shot_share_recent,
        afm.danger_zone_ratio_recent as away_danger_zone_ratio_recent,
        afm.shot_accuracy_recent as away_shot_accuracy_recent,
        afm.finishing_efficiency_recent as away_finishing_efficiency_recent,
        afm.pass_accuracy_recent as away_pass_accuracy_recent,
        afm.passes_per_match_recent as away_passes_per_match_recent,
        afm.corner_kicks_per_match_recent as away_corner_kicks_per_match_recent,
        afm.corners_conceded_per_match_recent as away_corners_conceded_per_match_recent,
        afm.save_ratio_recent as away_save_ratio_recent,

        not coalesce(hfm.is_tournament_form, false) as home_form_from_qualifiers,
        not coalesce(afm.is_tournament_form, false) as away_form_from_qualifiers
    from import_int_matchday__upcoming_round_fixtures as um
    left join mart_team_season as home_ts
        on
            um.home_team_sk = home_ts.team_sk
            and um.season_sk = home_ts.season_sk
    left join mart_team_season as away_ts
        on
            um.away_team_sk = away_ts.team_sk
            and um.season_sk = away_ts.season_sk
    left join dim_team as home_dt
        on um.home_team_sk = home_dt.team_sk
    left join dim_team as away_dt
        on um.away_team_sk = away_dt.team_sk
    left join home_form_matchday as hfm
        on
            um.fixture_sk = hfm.fixture_sk
            and um.home_team_sk = hfm.home_team_sk
    left join away_form_matchday as afm
        on
            um.fixture_sk = afm.fixture_sk
            and um.away_team_sk = afm.away_team_sk
)

select *
from final
order by fixture_date asc, kickoff_datetime asc, fixture_sk asc
