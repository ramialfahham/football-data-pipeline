{{
    config(
        tags=["dq", "mart", "season_insights"],
        store_failures = true
    )
}}

-- Fails when derived season rates are inconsistent with underlying sums (same rules as matchday form).

with src as (
    select
        i.*,
        m.games_expecting_team_stats
    from {{ ref('mart_team_season_insights') }} as i
    inner join {{ ref('int_team_season__metrics') }} as m
        on i.team_season_sk = m.team_season_sk
    where i.season_games_played > 0
),

checks as (
    select
        team_season_sk,
        team_sk,
        league_code,

        -- A per-match rate divides by the played matches: a forfeit counts in the season's goals and
        -- points but in no rate, so the three scoreline checks hold the rate to the total only for a
        -- team that had none. The formula recompute covers the rest.
        case
            when goals_per_match is null or goals_for_sum_season is null then 0
            when games_expecting_team_stats != season_games_played then 0
            else abs(goals_per_match * season_games_played - goals_for_sum_season)
        end as goals_per_match_err,
        case
            when goals_against_per_match is null or goals_against_sum_season is null then 0
            when games_expecting_team_stats != season_games_played then 0
            else abs(goals_against_per_match * season_games_played - goals_against_sum_season)
        end as goals_against_per_match_err,
        case
            when points_capture_pct is null or points_won_sum_season is null then 0
            when games_expecting_team_stats != season_games_played then 0
            else abs(points_capture_pct * (3 * season_games_played) - points_won_sum_season)
        end as points_capture_pct_err,
        -- the season shot total leaves a forfeit out, like the rate, so the two hold over the
        -- played matches for every team
        case
            when shots_per_match is null or total_shots_sum_season is null then 0
            else abs(shots_per_match * games_expecting_team_stats - total_shots_sum_season)
        end as shots_per_match_err,
        -- season_games_played is sourced independently of the stat line, and is itself checked
        -- against the standings' played count, so bounding coverage by it puts a second, unrelated
        -- number in the way. A game can carry a team stat line only if it was played.
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
