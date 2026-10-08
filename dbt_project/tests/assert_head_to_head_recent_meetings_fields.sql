-- Fail any recent meeting with a blank field, a result other than W/D/L or a side other than home/away,
-- any row whose list does not hold its ten most recent meetings, and any meeting whose mirror row
-- (the opponent's side of the same pair) lacks it or gives the same home or away side.
{{ config(store_failures = true) }}

with h2h as (
    select
        team_sk,
        opponent_team_sk,
        total_meetings,
        recent_meetings
    from {{ ref('mart_head_to_head') }}
)

select
    h.team_sk,
    h.opponent_team_sk,
    'field' as failure
from h2h as h, unnest(h.recent_meetings) as m
where
    m.kickoff_datetime is null
    or m.league_code is null
    or m.goals_for is null
    or m.goals_against is null
    or m.result is null
    or m.result not in ('W', 'D', 'L')
    or m.home_away is null
    or m.home_away not in ('home', 'away')

union all

select
    team_sk,
    opponent_team_sk,
    'length' as failure
from h2h
where coalesce(array_length(recent_meetings), 0) != least(total_meetings, 10)

union all

select
    h.team_sk,
    h.opponent_team_sk,
    'mirror' as failure
from h2h as h, unnest(h.recent_meetings) as m
left join (
    select
        o.team_sk,
        o.opponent_team_sk,
        om.kickoff_datetime,
        om.home_away
    from h2h as o, unnest(o.recent_meetings) as om
) as mirror
    on
        h.opponent_team_sk = mirror.team_sk
        and h.team_sk = mirror.opponent_team_sk
        and m.kickoff_datetime = mirror.kickoff_datetime
where mirror.team_sk is null or mirror.home_away = m.home_away
