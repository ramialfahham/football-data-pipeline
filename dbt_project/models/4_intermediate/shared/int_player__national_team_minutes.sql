{#
  A player's minutes for a national team since 1 July 2025, beside the team's own minutes over
  the same matches: the length of each of its matches with player data, 90, or 120 after extra
  time. A regular played at least a third of the team's minutes.

  Grain: (player_sk, team_sk).
#}

with legs as (
    select
        player_sk,
        team_sk,
        fixture_sk,
        minutes
    from {{ ref('int_legs__player_match') }}
    where
        entity_type = 'national'
        and date(kickoff_datetime) >= date '2025-07-01'
),

matches as (
    select
        l.team_sk,
        l.fixture_sk,
        {{ one_value("if(f.status_short in ('AET', 'PEN'), 120, 90)") }} as match_minutes
    from legs as l
    inner join {{ ref('fct_fixture') }} as f
        on l.fixture_sk = f.fixture_sk
    group by l.team_sk, l.fixture_sk
),

team_minutes as (
    select
        team_sk,
        sum(match_minutes) as national_team_match_minutes
    from matches
    group by team_sk
),

player_minutes as (
    select
        player_sk,
        team_sk,
        coalesce(sum(minutes), 0) as national_team_minutes
    from legs
    group by player_sk, team_sk
)

select
    p.player_sk,
    p.team_sk,
    p.national_team_minutes,
    t.national_team_match_minutes,
    p.national_team_minutes * 3 >= t.national_team_match_minutes as is_regular
from player_minutes as p
inner join team_minutes as t
    on p.team_sk = t.team_sk
