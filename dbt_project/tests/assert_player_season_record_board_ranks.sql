-- The two Players to watch boards of mart_player_season_record. Fail a goalkeeper on either board, a
-- player on a board without its rule (a zero, below the minutes floor) or off it with the rule met, a
-- gap in a side's places, and any pair of neighbours out of the board's order.
{{ config(store_failures = true, severity = 'error') }}

with played as (
    select
        team_sk,
        league_code,
        season_api_year,
        countif(not is_awarded_result) as team_matches
    from {{ ref('int_legs__team_match') }}
    group by team_sk, league_code, season_api_year
),

side_rows as (
    select
        r.upcoming_fixture_sk,
        r.team_sk,
        r.player_sk,
        r.scorer_points_player,
        r.goals_total,
        r.ball_actions_per90,
        r.minutes,
        r.scorer_points_rank,
        r.ball_actions_per90_rank,
        coalesce(
            r.position_code != 'G',
            p.player_position != 'Goalkeeper',
            true
        ) as is_outfield,
        r.minutes >= pl.team_matches * 90 / 3 as meets_floor
    from {{ ref('mart_player_season_record') }} as r
    left join {{ ref('dim_player') }} as p
        on r.player_sk = p.player_sk
    left join played as pl
        on
            r.team_sk = pl.team_sk
            and r.league_code = pl.league_code
            and r.season_api_year = pl.season_api_year
),

points as (
    select
        *,
        row_number() over w as place,
        lead(scorer_points_player) over w as next_points,
        lead(goals_total) over w as next_goals,
        lead(minutes) over w as next_minutes,
        lead(player_sk) over w as next_player_sk
    from side_rows
    where scorer_points_rank is not null
    window w as (partition by upcoming_fixture_sk, team_sk order by scorer_points_rank)
),

actions as (
    select
        *,
        row_number() over w as place,
        lead(ball_actions_per90) over w as next_value,
        lead(minutes) over w as next_minutes,
        lead(player_sk) over w as next_player_sk
    from side_rows
    where ball_actions_per90_rank is not null
    window w as (partition by upcoming_fixture_sk, team_sk order by ball_actions_per90_rank)
)

select
    upcoming_fixture_sk,
    team_sk,
    player_sk,
    'goalkeeper on a board' as failure
from side_rows
where
    not is_outfield
    and (scorer_points_rank is not null or ball_actions_per90_rank is not null)

union all

select
    upcoming_fixture_sk,
    team_sk,
    player_sk,
    'goals and assists board without its rule' as failure
from side_rows
where scorer_points_rank is not null and not coalesce(scorer_points_player > 0, false)

union all

select
    upcoming_fixture_sk,
    team_sk,
    player_sk,
    'outfield scorer left off the goals and assists board' as failure
from side_rows
where scorer_points_rank is null and is_outfield and scorer_points_player > 0

union all

select
    upcoming_fixture_sk,
    team_sk,
    player_sk,
    'ball actions board without its rule' as failure
from side_rows
where
    ball_actions_per90_rank is not null
    and not coalesce(ball_actions_per90 > 0 and meets_floor, false)

union all

select
    upcoming_fixture_sk,
    team_sk,
    player_sk,
    'qualified outfield player left off the ball actions board' as failure
from side_rows
where
    ball_actions_per90_rank is null
    and is_outfield
    and ball_actions_per90 > 0
    and meets_floor

union all

select
    upcoming_fixture_sk,
    team_sk,
    player_sk,
    'gap in the goals and assists places' as failure
from points
where scorer_points_rank != place

union all

select
    upcoming_fixture_sk,
    team_sk,
    player_sk,
    'gap in the ball actions places' as failure
from actions
where ball_actions_per90_rank != place

union all

select
    upcoming_fixture_sk,
    team_sk,
    player_sk,
    'goals and assists out of order' as failure
from points
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

union all

select
    upcoming_fixture_sk,
    team_sk,
    player_sk,
    'ball actions per 90 out of order' as failure
from actions
where
    next_player_sk is not null
    and not coalesce(
        ball_actions_per90 > next_value
        or (ball_actions_per90 = next_value and minutes >= next_minutes),
        false
    )
