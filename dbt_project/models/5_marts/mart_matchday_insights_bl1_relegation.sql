{{ config(materialized='view') }}

{#
  BL1 relegation play-off matchday surface. Same metric columns as mart_matchday_insights;
  form uses each team's domestic league (BL1 or BL2) via int_matchday__team_form_metrics_relegation.
  Standings join on form league + form season, not the BL1 fixture season_sk alone.
#}

with import_int_matchday__relegation_upcoming_fixtures as (
    select * from {{ ref('int_matchday__relegation_upcoming_fixtures') }}
),

import_int_matchday__team_form_metrics_relegation as (
    select * from {{ ref('int_matchday__team_form_metrics_relegation') }}
),

mart_team_season as (
    select * from {{ ref('mart_team_season') }}
),

dim_team as (
    select * from {{ ref('dim_team') }}
),

team_form_metrics as (
    select * from import_int_matchday__team_form_metrics_relegation
),

home_form as (
    select
        fixture_sk,
        team_sk as home_team_sk,
        form_league_code as home_form_league_code,
        form_season_api_year,
        form_games_played as home_form_games_played,
        form_matchdays_used as home_form_matchdays_used,
        stat_coverage_form_games as home_stat_coverage_form_games,
        points_won_sum_form as home_points_won_sum_form,
        goals_for_sum_form as home_goals_for_sum_form,
        goals_against_sum_form as home_goals_against_sum_form,
        total_shots_sum_form as home_total_shots_sum_form,
        opponent_total_shots_sum_form as home_opponent_total_shots_sum_form,
        shots_inside_box_sum_form as home_shots_inside_box_sum_form,
        shots_on_goal_sum_form as home_shots_on_goal_sum_form,
        corner_kicks_sum_form as home_corner_kicks_sum_form,
        opponent_corner_kicks_sum_form as home_opponent_corner_kicks_sum_form,
        passes_accurate_sum_form as home_passes_accurate_sum_form,
        passes_total_sum_form as home_passes_total_sum_form,
        goalkeeper_saves_sum_form as home_goalkeeper_saves_sum_form,
        points_capture_recent as home_points_capture_recent,
        goals_per_match_recent as home_goals_per_match_recent,
        goals_against_per_match_recent as home_goals_against_per_match_recent,
        shots_per_match_recent as home_shots_per_match_recent,
        shot_share_recent as home_shot_share_recent,
        danger_zone_ratio_recent as home_danger_zone_ratio_recent,
        shot_accuracy_recent as home_shot_accuracy_recent,
        finishing_efficiency_recent as home_finishing_efficiency_recent,
        pass_accuracy_recent as home_pass_accuracy_recent,
        passes_per_match_recent as home_passes_per_match_recent,
        corner_kicks_per_match_recent as home_corner_kicks_per_match_recent,
        corners_conceded_per_match_recent as home_corners_conceded_per_match_recent,
        save_ratio_recent as home_save_ratio_recent
    from team_form_metrics
),

away_form as (
    select
        fixture_sk,
        team_sk as away_team_sk,
        form_league_code as away_form_league_code,
        form_games_played as away_form_games_played,
        form_matchdays_used as away_form_matchdays_used,
        stat_coverage_form_games as away_stat_coverage_form_games,
        points_won_sum_form as away_points_won_sum_form,
        goals_for_sum_form as away_goals_for_sum_form,
        goals_against_sum_form as away_goals_against_sum_form,
        total_shots_sum_form as away_total_shots_sum_form,
        opponent_total_shots_sum_form as away_opponent_total_shots_sum_form,
        shots_inside_box_sum_form as away_shots_inside_box_sum_form,
        shots_on_goal_sum_form as away_shots_on_goal_sum_form,
        corner_kicks_sum_form as away_corner_kicks_sum_form,
        opponent_corner_kicks_sum_form as away_opponent_corner_kicks_sum_form,
        passes_accurate_sum_form as away_passes_accurate_sum_form,
        passes_total_sum_form as away_passes_total_sum_form,
        goalkeeper_saves_sum_form as away_goalkeeper_saves_sum_form,
        points_capture_recent as away_points_capture_recent,
        goals_per_match_recent as away_goals_per_match_recent,
        goals_against_per_match_recent as away_goals_against_per_match_recent,
        shots_per_match_recent as away_shots_per_match_recent,
        shot_share_recent as away_shot_share_recent,
        danger_zone_ratio_recent as away_danger_zone_ratio_recent,
        shot_accuracy_recent as away_shot_accuracy_recent,
        finishing_efficiency_recent as away_finishing_efficiency_recent,
        pass_accuracy_recent as away_pass_accuracy_recent,
        passes_per_match_recent as away_passes_per_match_recent,
        corner_kicks_per_match_recent as away_corner_kicks_per_match_recent,
        corners_conceded_per_match_recent as away_corners_conceded_per_match_recent,
        save_ratio_recent as away_save_ratio_recent
    from team_form_metrics
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
        home_dt.team_logo_url as home_team_logo_url,
        away_dt.team_logo_url as away_team_logo_url,
        hf.home_form_league_code,
        af.away_form_league_code,
        home_ts.latest_rank as home_league_rank,
        away_ts.latest_rank as away_league_rank,
        home_ts.standings_group_description as home_standings_group_description,
        away_ts.standings_group_description as away_standings_group_description,
        hf.form_season_api_year,
        hf.home_form_games_played,
        hf.home_form_matchdays_used,
        hf.home_stat_coverage_form_games,
        hf.home_points_won_sum_form,
        hf.home_goals_for_sum_form,
        hf.home_goals_against_sum_form,
        hf.home_total_shots_sum_form,
        hf.home_opponent_total_shots_sum_form,
        hf.home_shots_inside_box_sum_form,
        hf.home_shots_on_goal_sum_form,
        hf.home_corner_kicks_sum_form,
        hf.home_opponent_corner_kicks_sum_form,
        hf.home_passes_accurate_sum_form,
        hf.home_passes_total_sum_form,
        hf.home_goalkeeper_saves_sum_form,
        hf.home_points_capture_recent,
        hf.home_goals_per_match_recent,
        hf.home_goals_against_per_match_recent,
        hf.home_shots_per_match_recent,
        hf.home_shot_share_recent,
        hf.home_danger_zone_ratio_recent,
        hf.home_shot_accuracy_recent,
        hf.home_finishing_efficiency_recent,
        hf.home_pass_accuracy_recent,
        hf.home_passes_per_match_recent,
        hf.home_corner_kicks_per_match_recent,
        hf.home_corners_conceded_per_match_recent,
        hf.home_save_ratio_recent,
        af.away_form_games_played,
        af.away_form_matchdays_used,
        af.away_stat_coverage_form_games,
        af.away_points_won_sum_form,
        af.away_goals_for_sum_form,
        af.away_goals_against_sum_form,
        af.away_total_shots_sum_form,
        af.away_opponent_total_shots_sum_form,
        af.away_shots_inside_box_sum_form,
        af.away_shots_on_goal_sum_form,
        af.away_corner_kicks_sum_form,
        af.away_opponent_corner_kicks_sum_form,
        af.away_passes_accurate_sum_form,
        af.away_passes_total_sum_form,
        af.away_goalkeeper_saves_sum_form,
        af.away_points_capture_recent,
        af.away_goals_per_match_recent,
        af.away_goals_against_per_match_recent,
        af.away_shots_per_match_recent,
        af.away_shot_share_recent,
        af.away_danger_zone_ratio_recent,
        af.away_shot_accuracy_recent,
        af.away_finishing_efficiency_recent,
        af.away_pass_accuracy_recent,
        af.away_passes_per_match_recent,
        af.away_corner_kicks_per_match_recent,
        af.away_corners_conceded_per_match_recent,
        af.away_save_ratio_recent,
        'Bundesliga Relegation' as league_name
    from import_int_matchday__relegation_upcoming_fixtures as um
    left join home_form as hf
        on
            um.fixture_sk = hf.fixture_sk
            and um.home_team_sk = hf.home_team_sk
    left join away_form as af
        on
            um.fixture_sk = af.fixture_sk
            and um.away_team_sk = af.away_team_sk
    left join mart_team_season as home_ts
        on
            um.home_team_sk = home_ts.team_sk
            and hf.home_form_league_code = home_ts.league_code
            and hf.form_season_api_year = home_ts.season_api_year
    left join mart_team_season as away_ts
        on
            um.away_team_sk = away_ts.team_sk
            and af.away_form_league_code = away_ts.league_code
            and hf.form_season_api_year = away_ts.season_api_year
    left join dim_team as home_dt
        on um.home_team_sk = home_dt.team_sk
    left join dim_team as away_dt
        on um.away_team_sk = away_dt.team_sk
)

select *
from final
order by fixture_date asc, kickoff_datetime asc, fixture_sk asc
