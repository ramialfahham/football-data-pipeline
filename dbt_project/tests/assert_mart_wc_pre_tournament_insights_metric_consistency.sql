{{
    config(
        tags=["dq", "mart", "wc", "pretournament"]
    )
}}

-- When a completeness flag is true, derived pretournament rates must match underlying sums.

with src as (
    select * from {{ ref('mart_wc_pre_tournament_insights') }}
    where qualifier_games_played > 0
),

checks as (
    select
        team_sk,
        league_code,

        case
            when not is_goals_per_match_complete then 0
            when goals_per_match_pretournament is null or goals_for_sum_pretournament is null then 0
            else abs(goals_per_match_pretournament * qualifier_games_played - goals_for_sum_pretournament)
        end as goals_per_match_err,
        case
            when not is_goals_against_per_match_complete then 0
            when goals_against_per_match_pretournament is null or goals_against_sum_pretournament is null then 0
            else abs(
                goals_against_per_match_pretournament * qualifier_games_played - goals_against_sum_pretournament
            )
        end as goals_against_per_match_err,
        case
            when not is_points_capture_complete then 0
            when points_capture_pretournament is null or points_won_sum_pretournament is null then 0
            else abs(points_capture_pretournament * (3 * qualifier_games_played) - points_won_sum_pretournament)
        end as points_capture_err,
        case
            when not is_shots_per_match_complete then 0
            when shots_per_match_pretournament is null or total_shots_sum_pretournament is null then 0
            else abs(shots_per_match_pretournament * qualifier_games_played - total_shots_sum_pretournament)
        end as shots_per_match_err
    from src
)

select *
from checks
where greatest(
    goals_per_match_err,
    goals_against_per_match_err,
    points_capture_err,
    shots_per_match_err
) > 0.001
