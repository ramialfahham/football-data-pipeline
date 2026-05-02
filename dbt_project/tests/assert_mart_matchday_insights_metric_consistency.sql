{{
    config(
        tags=["dq", "mart", "form_metrics"]
    )
}}

-- Fails if any derived rate or ratio metric is arithmetically inconsistent
-- with the underlying sum columns it was computed from.
-- Only checks rows where both teams have form data (form_games_played > 0).

with src as (
    select * from {{ ref('mart_matchday_insights') }}
),

checks as (
    select
        fixture_sk,
        home_team_sk,
        away_team_sk,

        abs(home_goals_per_match_recent * home_form_games_played - home_goals_for_sum_form)
            as home_goals_per_match_err,
        abs(away_goals_per_match_recent * away_form_games_played - away_goals_for_sum_form)
            as away_goals_per_match_err,

        abs(home_goals_against_per_match_recent * home_form_games_played - home_goals_against_sum_form)
            as home_goals_against_per_match_err,
        abs(away_goals_against_per_match_recent * away_form_games_played - away_goals_against_sum_form)
            as away_goals_against_per_match_err,

        abs(home_shots_per_match_recent * home_form_games_played - home_total_shots_sum_form)
            as home_shots_per_match_err,
        abs(away_shots_per_match_recent * away_form_games_played - away_total_shots_sum_form)
            as away_shots_per_match_err,

        abs(home_passes_per_match_recent * home_form_games_played - home_passes_total_sum_form)
            as home_passes_per_match_err,
        abs(away_passes_per_match_recent * away_form_games_played - away_passes_total_sum_form)
            as away_passes_per_match_err,

        abs(home_corner_kicks_per_match_recent * home_form_games_played - home_corner_kicks_sum_form)
            as home_corners_per_match_err,
        abs(away_corner_kicks_per_match_recent * away_form_games_played - away_corner_kicks_sum_form)
            as away_corners_per_match_err,

        abs(home_points_capture_recent * 3 * home_form_games_played - home_points_won_sum_form)
            as home_points_capture_err,
        abs(away_points_capture_recent * 3 * away_form_games_played - away_points_won_sum_form)
            as away_points_capture_err,

        abs(home_pass_accuracy_recent * home_passes_total_sum_form - home_passes_accurate_sum_form)
            as home_pass_accuracy_err,
        abs(away_pass_accuracy_recent * away_passes_total_sum_form - away_passes_accurate_sum_form)
            as away_pass_accuracy_err,

        abs(home_shot_accuracy_recent * home_total_shots_sum_form - home_shots_on_goal_sum_form)
            as home_shot_accuracy_err,
        abs(away_shot_accuracy_recent * away_total_shots_sum_form - away_shots_on_goal_sum_form)
            as away_shot_accuracy_err,

        abs(home_danger_zone_ratio_recent * home_total_shots_sum_form - home_shots_inside_box_sum_form)
            as home_danger_zone_err,
        abs(away_danger_zone_ratio_recent * away_total_shots_sum_form - away_shots_inside_box_sum_form)
            as away_danger_zone_err,

        abs(
            home_save_ratio_recent
            * (home_goalkeeper_saves_sum_form + home_goals_against_sum_form)
            - home_goalkeeper_saves_sum_form
        ) as home_save_ratio_err,
        abs(
            away_save_ratio_recent
            * (away_goalkeeper_saves_sum_form + away_goals_against_sum_form)
            - away_goalkeeper_saves_sum_form
        ) as away_save_ratio_err

    from src
    where
        home_form_games_played > 0
        and away_form_games_played > 0
)

select *
from checks
where
    home_goals_per_match_err > 0.0001
    or away_goals_per_match_err > 0.0001
    or home_goals_against_per_match_err > 0.0001
    or away_goals_against_per_match_err > 0.0001
    or home_shots_per_match_err > 0.0001
    or away_shots_per_match_err > 0.0001
    or home_passes_per_match_err > 0.0001
    or away_passes_per_match_err > 0.0001
    or home_corners_per_match_err > 0.0001
    or away_corners_per_match_err > 0.0001
    or home_points_capture_err > 0.0001
    or away_points_capture_err > 0.0001
    or home_pass_accuracy_err > 0.0001
    or away_pass_accuracy_err > 0.0001
    or home_shot_accuracy_err > 0.0001
    or away_shot_accuracy_err > 0.0001
    or home_danger_zone_err > 0.0001
    or away_danger_zone_err > 0.0001
    or home_save_ratio_err > 0.0001
    or away_save_ratio_err > 0.0001
