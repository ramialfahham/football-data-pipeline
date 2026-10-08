-- top_player_rank orders a side by goals plus assists, then goals, then fewer minutes (unknown minutes
-- last). Fail a rank present without its goals plus assists or missing with them, a gap in a side's
-- ranks, and any pair of neighbours out of that order.
{{ config(store_failures = true, severity = 'error') }}

with ranked as (
    select
        upcoming_fixture_sk,
        team_sk,
        player_sk,
        top_player_rank,
        scorer_points_player,
        goals_total,
        minutes,
        row_number() over w as position,
        lead(scorer_points_player) over w as next_points,
        lead(goals_total) over w as next_goals,
        lead(minutes) over w as next_minutes,
        lead(player_sk) over w as next_player_sk
    from {{ ref('mart_player_season_record') }}
    where top_player_rank is not null
    window w as (partition by upcoming_fixture_sk, team_sk order by top_player_rank)
)

select
    upcoming_fixture_sk,
    team_sk,
    player_sk,
    'rank without goals plus assists, or goals plus assists without rank' as failure
from {{ ref('mart_player_season_record') }}
where (top_player_rank is null) != (scorer_points_player is null)

union all

select
    upcoming_fixture_sk,
    team_sk,
    player_sk,
    'gap in the ranks' as failure
from ranked
where top_player_rank != position

union all

select
    upcoming_fixture_sk,
    team_sk,
    player_sk,
    'out of order with the next rank' as failure
from ranked
where
    next_player_sk is not null
    and not coalesce(
        scorer_points_player > next_points
        or (scorer_points_player = next_points and goals_total > next_goals)
        or (
            scorer_points_player = next_points
            and goals_total = next_goals
            and (next_minutes is null or (minutes is not null and minutes <= next_minutes))
        ),
        false
    )
