{{
    config(
        tags=["dq", "mart", "season_profile"]
    )
}}

-- Fails when derived season rates are inconsistent with underlying sums (same rules as matchday form).

with src as (
    select * from {{ ref('mart_team_season_profile') }}
    where season_games_played > 0
),

checks as (
    select
        team_season_sk,
        team_sk,
        league_code,

        case
            when goals_per_match_season is null or goals_for_sum_season is null then 0
            else abs(goals_per_match_season * season_games_played - goals_for_sum_season)
        end as goals_per_match_err,
        case
            when goals_against_per_match_season is null or goals_against_sum_season is null then 0
            else abs(goals_against_per_match_season * season_games_played - goals_against_sum_season)
        end as goals_against_per_match_err,
        case
            when points_capture_season is null or points_won_sum_season is null then 0
            else abs(points_capture_season * (3 * season_games_played) - points_won_sum_season)
        end as points_capture_err,
        case
            when shots_per_match_season is null or total_shots_sum_season is null then 0
            else abs(shots_per_match_season * season_games_played - total_shots_sum_season)
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
