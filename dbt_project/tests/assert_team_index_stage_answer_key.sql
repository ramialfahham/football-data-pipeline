-- mart_team_index against team_index_answer_key: a club's cup_points is the sum of its rows in its
-- region's top club competition; a national team's world_cup_stage and championship_stage are
-- its World Cup row and its championship row.

with answer_key as (
    select * from {{ ref('team_index_answer_key') }}
),

regions as (
    select
        top_club_competition,
        continental_championship
    from {{ ref('confederations') }}
),

registry as (
    select
        league_code,
        competition_type
    from {{ ref('competition_registry') }}
),

team_index as (
    select * from {{ ref('mart_team_index') }}
),

club_expected as (
    select
        k.team_id,
        sum(k.stage_value) as expected_cup_points
    from answer_key as k
    inner join regions as g
        on k.league_code = g.top_club_competition
    group by k.team_id
),

national_expected as (
    select
        k.team_id,
        max(if(r.competition_type = 'world_championship', k.stage_value, null))
            as expected_world_cup_stage,
        max(if(g.continental_championship is not null, k.stage_value, null))
            as expected_championship_stage
    from answer_key as k
    inner join registry as r
        on k.league_code = r.league_code
    left join regions as g
        on k.league_code = g.continental_championship
    where r.competition_type = 'world_championship' or g.continental_championship is not null
    group by k.team_id
)

select
    c.team_id,
    'cup_points' as served_column,
    c.expected_cup_points as expected_value,
    t.cup_points as served_value
from club_expected as c
left join team_index as t
    on c.team_id = t.team_sk
where t.cup_points is distinct from c.expected_cup_points

union all

select
    n.team_id,
    'world_cup_stage' as served_column,
    n.expected_world_cup_stage as expected_value,
    t.world_cup_stage as served_value
from national_expected as n
left join team_index as t
    on n.team_id = t.team_sk
where t.world_cup_stage is distinct from n.expected_world_cup_stage

union all

select
    n.team_id,
    'championship_stage' as served_column,
    n.expected_championship_stage as expected_value,
    t.championship_stage as served_value
from national_expected as n
left join team_index as t
    on n.team_id = t.team_sk
where t.championship_stage is distinct from n.expected_championship_stage
