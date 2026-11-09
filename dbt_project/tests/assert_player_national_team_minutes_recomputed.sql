-- int_player__national_team_minutes against a recount from the core stat lines: every player's
-- minutes for a national team since 1 July 2025 and the team's minutes over its matches with stat
-- lines, 90 a match, 120 after extra time. Returns every pair that differs or is missing.

with lines as (
    select
        s.player_sk,
        s.team_sk,
        s.fixture_sk,
        s.minutes,
        f.status_short
    from {{ ref('fct_fixture_player_stats') }} as s
    inner join {{ ref('fct_fixture') }} as f
        on s.fixture_sk = f.fixture_sk
    inner join {{ ref('dim_league') }} as c
        on s.league_code = c.league_code
    where
        c.entity_type = 'national'
        and f.status_short in ('FT', 'AET', 'PEN')
        and f.goals_home is not null
        and f.goals_away is not null
        and date(f.kickoff_datetime) >= date '2025-07-01'
),

team_minutes as (
    select
        team_sk,
        sum(if(status_short in ('AET', 'PEN'), 120, 90)) as match_minutes
    from (
        select distinct
            team_sk,
            fixture_sk,
            status_short
        from lines
    )
    group by team_sk
),

expected as (
    select
        l.player_sk,
        l.team_sk,
        coalesce(sum(l.minutes), 0) as minutes,
        min(t.match_minutes) as match_minutes
    from lines as l
    inner join team_minutes as t
        on l.team_sk = t.team_sk
    group by l.player_sk, l.team_sk
),

served as (
    select * from {{ ref('int_player__national_team_minutes') }}
)

select
    e.minutes as expected_minutes,
    s.national_team_minutes,
    e.match_minutes as expected_match_minutes,
    s.national_team_match_minutes,
    coalesce(e.player_sk, s.player_sk) as player_sk,
    coalesce(e.team_sk, s.team_sk) as team_sk
from expected as e
full outer join served as s
    on e.player_sk = s.player_sk and e.team_sk = s.team_sk
where
    e.player_sk is null
    or s.player_sk is null
    or e.minutes != s.national_team_minutes
    or e.match_minutes != s.national_team_match_minutes
