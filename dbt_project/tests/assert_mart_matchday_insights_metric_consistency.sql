{{
    config(
        tags=["dq", "mart", "form_metrics"]
    )
}}

-- Fails if any derived rate or ratio metric is arithmetically inconsistent
-- with the underlying sum columns it was computed from.
-- Only rows where both teams have form data (form_games_played > 0).
-- Skips comparisons when the displayed rate or a required sum is null (honest nulls).
-- Domestic and WC marts checked separately (WC has extra UI columns).

with checks as (
    {{ matchday_metric_consistency_checks(ref('mart_matchday_insights')) }}
    union all
    {{ matchday_metric_consistency_checks(ref('mart_matchday_insights_wc')) }}
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
