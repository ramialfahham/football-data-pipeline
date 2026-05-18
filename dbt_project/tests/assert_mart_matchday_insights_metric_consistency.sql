{{
    config(
        tags=["dq", "mart", "form_metrics"]
    )
}}

-- Fails if any derived rate or ratio metric is arithmetically inconsistent
-- with the underlying sum columns it was computed from.
-- Only rows where both teams have form data (form_games_played > 0).
-- Skips comparisons when the displayed rate or a required sum is null (honest nulls).
-- Source: BL1 + WC marts (export view mart_matchday_insights is BL1-only for Pages until multi-UI).

with src as (
    select * from {{ ref('mart_matchday_insights_bl1') }}
    union all
    select * from {{ ref('mart_matchday_insights_pl') }}
    union all
    select * from {{ ref('mart_matchday_insights_pd') }}
    union all
    select * from {{ ref('mart_matchday_insights_bl2') }}
    union all
    select * from {{ ref('mart_matchday_insights_wc') }}
),

checks as (
    select
        fixture_sk,
        home_team_sk,
        away_team_sk,

        case
            when home_goals_per_match_recent is null or home_goals_for_sum_form is null then 0
            else abs(home_goals_per_match_recent * home_form_games_played - home_goals_for_sum_form)
        end as home_goals_per_match_err,
        case
            when away_goals_per_match_recent is null or away_goals_for_sum_form is null then 0
            else abs(away_goals_per_match_recent * away_form_games_played - away_goals_for_sum_form)
        end as away_goals_per_match_err,

        case
            when home_goals_against_per_match_recent is null or home_goals_against_sum_form is null then 0
            else abs(home_goals_against_per_match_recent * home_form_games_played - home_goals_against_sum_form)
        end as home_goals_against_per_match_err,
        case
            when away_goals_against_per_match_recent is null or away_goals_against_sum_form is null then 0
            else abs(away_goals_against_per_match_recent * away_form_games_played - away_goals_against_sum_form)
        end as away_goals_against_per_match_err,

        case
            when home_shots_per_match_recent is null or home_total_shots_sum_form is null then 0
            else abs(home_shots_per_match_recent * home_form_games_played - home_total_shots_sum_form)
        end as home_shots_per_match_err,
        case
            when away_shots_per_match_recent is null or away_total_shots_sum_form is null then 0
            else abs(away_shots_per_match_recent * away_form_games_played - away_total_shots_sum_form)
        end as away_shots_per_match_err,

        case
            when home_passes_per_match_recent is null or home_passes_total_sum_form is null then 0
            else abs(home_passes_per_match_recent * home_form_games_played - home_passes_total_sum_form)
        end as home_passes_per_match_err,
        case
            when away_passes_per_match_recent is null or away_passes_total_sum_form is null then 0
            else abs(away_passes_per_match_recent * away_form_games_played - away_passes_total_sum_form)
        end as away_passes_per_match_err,

        case
            when home_corner_kicks_per_match_recent is null or home_corner_kicks_sum_form is null then 0
            else abs(home_corner_kicks_per_match_recent * home_form_games_played - home_corner_kicks_sum_form)
        end as home_corners_per_match_err,
        case
            when away_corner_kicks_per_match_recent is null or away_corner_kicks_sum_form is null then 0
            else abs(away_corner_kicks_per_match_recent * away_form_games_played - away_corner_kicks_sum_form)
        end as away_corners_per_match_err,

        case
            when home_points_capture_recent is null or home_points_won_sum_form is null then 0
            else abs(home_points_capture_recent * 3 * home_form_games_played - home_points_won_sum_form)
        end as home_points_capture_err,
        case
            when away_points_capture_recent is null or away_points_won_sum_form is null then 0
            else abs(away_points_capture_recent * 3 * away_form_games_played - away_points_won_sum_form)
        end as away_points_capture_err,

        case
            when
                home_pass_accuracy_recent is null
                or home_passes_total_sum_form is null
                or home_passes_accurate_sum_form is null
                or home_passes_total_sum_form = 0
                then 0
            else abs(home_pass_accuracy_recent * home_passes_total_sum_form - home_passes_accurate_sum_form)
        end as home_pass_accuracy_err,
        case
            when
                away_pass_accuracy_recent is null
                or away_passes_total_sum_form is null
                or away_passes_accurate_sum_form is null
                or away_passes_total_sum_form = 0
                then 0
            else abs(away_pass_accuracy_recent * away_passes_total_sum_form - away_passes_accurate_sum_form)
        end as away_pass_accuracy_err,

        case
            when
                home_shot_accuracy_recent is null
                or home_total_shots_sum_form is null
                or home_shots_on_goal_sum_form is null
                or home_total_shots_sum_form = 0
                then 0
            else abs(home_shot_accuracy_recent * home_total_shots_sum_form - home_shots_on_goal_sum_form)
        end as home_shot_accuracy_err,
        case
            when
                away_shot_accuracy_recent is null
                or away_total_shots_sum_form is null
                or away_shots_on_goal_sum_form is null
                or away_total_shots_sum_form = 0
                then 0
            else abs(away_shot_accuracy_recent * away_total_shots_sum_form - away_shots_on_goal_sum_form)
        end as away_shot_accuracy_err,

        case
            when
                home_danger_zone_ratio_recent is null
                or home_total_shots_sum_form is null
                or home_shots_inside_box_sum_form is null
                or home_total_shots_sum_form = 0
                then 0
            else abs(home_danger_zone_ratio_recent * home_total_shots_sum_form - home_shots_inside_box_sum_form)
        end as home_danger_zone_err,
        case
            when
                away_danger_zone_ratio_recent is null
                or away_total_shots_sum_form is null
                or away_shots_inside_box_sum_form is null
                or away_total_shots_sum_form = 0
                then 0
            else abs(away_danger_zone_ratio_recent * away_total_shots_sum_form - away_shots_inside_box_sum_form)
        end as away_danger_zone_err,

        case
            when
                home_save_ratio_recent is null
                or home_goalkeeper_saves_sum_form is null
                or home_goals_against_sum_form is null
                or (coalesce(home_goalkeeper_saves_sum_form, 0) + coalesce(home_goals_against_sum_form, 0)) = 0
                then 0
            else abs(
                home_save_ratio_recent
                * (home_goalkeeper_saves_sum_form + home_goals_against_sum_form)
                - home_goalkeeper_saves_sum_form
            )
        end as home_save_ratio_err,
        case
            when
                away_save_ratio_recent is null
                or away_goalkeeper_saves_sum_form is null
                or away_goals_against_sum_form is null
                or (coalesce(away_goalkeeper_saves_sum_form, 0) + coalesce(away_goals_against_sum_form, 0)) = 0
                then 0
            else abs(
                away_save_ratio_recent
                * (away_goalkeeper_saves_sum_form + away_goals_against_sum_form)
                - away_goalkeeper_saves_sum_form
            )
        end as away_save_ratio_err

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
