{{
    config(
        tags=["dq", "mart", "season_insights"]
    )
}}

-- Fails when derived season rates are inconsistent with underlying sums (same rules as matchday form).

with src as (
    select * from {{ ref('mart_team_season_insights') }}
    where season_games_played > 0
),

checks as (
    select
        team_season_sk,
        team_sk,
        league_code,

        case
            when goals_per_match is null or goals_for_sum_season is null then 0
            else abs(goals_per_match * season_games_played - goals_for_sum_season)
        end as goals_per_match_err,
        case
            when goals_against_per_match is null or goals_against_sum_season is null then 0
            else abs(goals_against_per_match * season_games_played - goals_against_sum_season)
        end as goals_against_per_match_err,
        case
            when points_capture_pct is null or points_won_sum_season is null then 0
            else abs(points_capture_pct * (3 * season_games_played) - points_won_sum_season)
        end as points_capture_pct_err,
        -- ⚠ MULTIPLIES BY games_with_team_stats, NOT season_games_played, and the two are different
        -- numbers as soon as a team has an awarded match. shots_per_match divides by the games that
        -- CARRY a stat line; an AWD/WO result is a played game that has none and never will, so
        -- multiplying the rate back by played games overstates the sum by exactly one game's shots
        -- per awarded match. The three checks above keep season_games_played because goals, goals
        -- against and points are scoreline quantities and an awarded match has a real scoreline.
        case
            when shots_per_match is null or total_shots_sum_season is null then 0
            else abs(shots_per_match * games_with_team_stats - total_shots_sum_season)
        end as shots_per_match_err,
        -- ⚠ RESTORES A CROSS-CHECK THE LINE ABOVE WOULD OTHERWISE HAVE COST, and it is the reason
        -- this check exists rather than being obviously redundant. Multiplying by the same column
        -- the rate divides by makes that identity true, but it also makes it blind to an error in
        -- games_with_team_stats itself: numerator and multiplier now come from one value, so they
        -- cannot disagree. season_games_played is sourced independently — and is itself checked
        -- against the standings' played count — so bounding coverage by it puts a second, unrelated
        -- number back in the way. A game can carry a team stat line only if it was played.
        case
            when games_with_team_stats is null then 0
            else greatest(games_with_team_stats - season_games_played, 0)
        end as coverage_exceeds_played_err
    from src
)

select *
from checks
where greatest(
    goals_per_match_err,
    goals_against_per_match_err,
    points_capture_pct_err,
    shots_per_match_err,
    coverage_exceeds_played_err
) > 0.001
