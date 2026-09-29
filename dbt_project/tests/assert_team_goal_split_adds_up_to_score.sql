{{ config(severity = 'error', store_failures = true) }}

-- A team's goals are its open-play goals, its penalties and the own goals credited to it, nothing
-- else. Open-play goals are counted from the events here, so the model's goals_penalty and goals_own
-- are checked against the scoreline rather than against their own difference. The provider files an
-- own goal under the team it counts for, and a shoot-out kick is no goal. Only matches whose
-- attributable goal events add up to the score are checked: elsewhere the events are incomplete.
--
-- Three matches are left out because the provider's events disagree with the score on who scored:
-- 21650, Sassuolo v Pescara, Serie A 2016/17: awarded 0-3, the events keep the 2-1 played;
-- 247587, Flamengo v River Plate, Libertadores 2019 final: Flamengo's two late goals filed under River;
-- 1373026, AC Milan v Bologna, Coppa Italia 2025 final: Bologna's goal filed under Milan.

with goal_events as (
    select
        fixture_sk,
        team_sk,
        event_detail
    from {{ ref('fct_fixture_event') }}
    where
        event_type = 'Goal'
        and event_detail in ('Normal Goal', 'Penalty', 'Own Goal')
        and event_comments is distinct from 'Penalty Shootout'
        and team_sk is not null
),

open_play as (
    select
        fixture_sk,
        team_sk,
        countif(event_detail = 'Normal Goal') as goals_open_play_events
    from goal_events
    group by fixture_sk, team_sk
),

event_totals as (
    select
        fixture_sk,
        count(*) as goal_events
    from goal_events
    group by fixture_sk
),

covered as (
    select l.fixture_sk
    from {{ ref('int_legs__team_match') }} as l
    left join event_totals as t
        on l.fixture_sk = t.fixture_sk
    group by l.fixture_sk
    having sum(l.goals_for) = max(coalesce(t.goal_events, 0))
)

select
    l.fixture_sk,
    l.team_sk,
    l.league_code,
    l.goals_for,
    l.goals_penalty,
    l.goals_own,
    coalesce(o.goals_open_play_events, 0) as goals_open_play_events
from {{ ref('int_legs__team_match') }} as l
inner join covered as c
    on l.fixture_sk = c.fixture_sk
left join open_play as o
    on l.fixture_sk = o.fixture_sk and l.team_sk = o.team_sk
where
    l.fixture_sk not in (21650, 247587, 1373026)
    and coalesce(o.goals_open_play_events, 0) + l.goals_penalty + l.goals_own != l.goals_for
