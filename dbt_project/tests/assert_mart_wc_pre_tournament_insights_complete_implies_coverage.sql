{{
    config(
        tags=["dq", "mart", "wc", "pretournament"]
    )
}}

-- is_*_complete must not be true when there are no qualifier legs.

select
    team_sk,
    qualifier_games_played,
    is_shots_per_match_complete,
    is_goals_per_match_complete
from {{ ref('mart_wc_pre_tournament_insights') }}
where
    qualifier_games_played = 0
    and (
        is_points_capture_complete
        or is_goals_per_match_complete
        or is_goals_against_per_match_complete
        or is_shots_per_match_complete
        or is_shot_share_complete
        or is_danger_zone_ratio_complete
        or is_shot_accuracy_complete
        or is_finishing_efficiency_complete
        or is_pass_accuracy_complete
        or is_passes_per_match_complete
        or is_corner_kicks_per_match_complete
        or is_corners_conceded_per_match_complete
        or is_save_ratio_complete
    )
