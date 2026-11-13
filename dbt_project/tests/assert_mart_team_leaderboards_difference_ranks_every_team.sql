-- The shots-on-target difference board ranks every team, zero and negatives included (the
-- ranking_rules doc block: on a difference, zero is a value). Fail a team-season with a difference
-- that is missing from the board, a board out of value order, and a board with no negative row at
-- all, which is what the zero rule's cut would leave.
{{ config(store_failures = true) }}

with expected as (
    select
        team_sk,
        season_sk
    from {{ ref('int_team_season__metrics') }}
    where season_games_played >= 1 and shots_on_goal_difference_per_match is not null
),

served as (
    select
        team_sk,
        season_sk,
        sort_value,
        league_code,
        season_api_year,
        league_leader_order,
        lead(sort_value) over w as next_value
    from {{ ref('mart_team_leaderboards') }}
    where metric_key = 'shots_on_goal_difference_per_match'
    window w as (partition by league_code, season_api_year order by league_leader_order)
)

select
    cast(e.team_sk as string) as detail,
    'team-season missing from the difference board' as failure
from expected as e
left join served as s
    on e.team_sk = s.team_sk and e.season_sk = s.season_sk
where s.team_sk is null

union all

select
    cast(team_sk as string) as detail,
    'difference board out of value order' as failure
from served
where next_value > sort_value

union all

select
    'all' as detail,
    'no negative difference on the board' as failure
from (select countif(sort_value < 0) as negatives from served)
where negatives = 0
