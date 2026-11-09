{#
  A player's position is the one played most often, then the one from the most recent match, then
  the code. This recomputes it where a model picks one: the season on mart_player_profile, the
  season to date on int_player_season_record (its last row), and the form window on
  int_player_momentum__metrics. A position is the rule's pick when no other position beats it.
  Each failing row is a picked position that differs from the rule's.
#}
{{ config(store_failures = true, severity = 'error') }}

with profile_positions as (
    select
        s.player_sk,
        f.season_sk,
        s.position_code,
        count(*) as legs,
        max(f.kickoff_datetime) as last_kickoff
    from {{ ref('fct_fixture_player_stats') }} as s
    inner join {{ ref('fct_fixture') }} as f
        on s.fixture_sk = f.fixture_sk
    where
        f.status_short in ('FT', 'AET', 'PEN')
        and s.position_code is not null
    group by s.player_sk, f.season_sk, s.position_code
),

profile_expected as (
    select
        a.player_sk,
        a.season_sk,
        a.position_code
    from profile_positions as a
    left join profile_positions as b
        on
            a.player_sk = b.player_sk
            and a.season_sk = b.season_sk
            and (
                a.legs < b.legs
                or (a.legs = b.legs and a.last_kickoff < b.last_kickoff)
                or (a.legs = b.legs and a.last_kickoff = b.last_kickoff and a.position_code > b.position_code)
            )
    where b.player_sk is null
),

season_last_rows as (
    select
        team_sk,
        player_sk,
        league_code,
        season_api_year,
        kickoff_datetime,
        fixture_sk,
        position_code
    from {{ ref('int_player_season_record') }}
    qualify row_number() over (
        partition by team_sk, player_sk, league_code, season_api_year
        order by kickoff_datetime desc, fixture_sk desc
    ) = 1
),

-- The legs up to the model's last row: a later leg with unknown minutes has no row of its own.
season_positions as (
    select
        l.team_sk,
        l.player_sk,
        l.league_code,
        l.season_api_year,
        l.position_code,
        count(*) as legs,
        max(l.kickoff_datetime) as last_kickoff
    from {{ ref('int_legs__player_match') }} as l
    inner join season_last_rows as r
        on
            l.team_sk = r.team_sk
            and l.player_sk = r.player_sk
            and l.league_code = r.league_code
            and l.season_api_year = r.season_api_year
            and (
                l.kickoff_datetime < r.kickoff_datetime
                or (l.kickoff_datetime = r.kickoff_datetime and l.fixture_sk <= r.fixture_sk)
            )
    where
        (l.minutes > 0 or l.minutes is null)
        and l.position_code is not null
    group by l.team_sk, l.player_sk, l.league_code, l.season_api_year, l.position_code
),

season_expected as (
    select
        a.team_sk,
        a.player_sk,
        a.league_code,
        a.season_api_year,
        a.position_code
    from season_positions as a
    left join season_positions as b
        on
            a.team_sk = b.team_sk
            and a.player_sk = b.player_sk
            and a.league_code = b.league_code
            and a.season_api_year = b.season_api_year
            and (
                a.legs < b.legs
                or (a.legs = b.legs and a.last_kickoff < b.last_kickoff)
                or (a.legs = b.legs and a.last_kickoff = b.last_kickoff and a.position_code > b.position_code)
            )
    where b.player_sk is null
),

window_positions as (
    select
        w.upcoming_fixture_sk,
        w.team_sk,
        p.player_sk,
        p.position_code,
        count(*) as legs,
        max(p.kickoff_datetime) as last_kickoff
    from {{ ref('int_team_momentum_window') }} as w
    inner join {{ ref('int_legs__player_match') }} as p
        on
            w.leg_fixture_sk = p.fixture_sk
            and w.team_sk = p.team_sk
    where
        w.window_type != 'match'
        and w.upcoming_fixture_sk is not null
        and p.position_code is not null
    group by w.upcoming_fixture_sk, w.team_sk, p.player_sk, p.position_code
),

window_expected as (
    select
        a.upcoming_fixture_sk,
        a.team_sk,
        a.player_sk,
        a.position_code
    from window_positions as a
    left join window_positions as b
        on
            a.upcoming_fixture_sk = b.upcoming_fixture_sk
            and a.team_sk = b.team_sk
            and a.player_sk = b.player_sk
            and (
                a.legs < b.legs
                or (a.legs = b.legs and a.last_kickoff < b.last_kickoff)
                or (a.legs = b.legs and a.last_kickoff = b.last_kickoff and a.position_code > b.position_code)
            )
    where b.player_sk is null
)

select
    'mart_player_profile' as model_name,
    to_json_string(struct(p.player_sk, p.season_sk)) as group_key,
    p.position_code as picked_position,
    e.position_code as rule_position
from {{ ref('mart_player_profile') }} as p
left join profile_expected as e
    on p.player_sk = e.player_sk and p.season_sk = e.season_sk
where p.position_code is distinct from e.position_code

union all

select
    'int_player_season_record' as model_name,
    to_json_string(struct(r.team_sk, r.player_sk, r.league_code, r.season_api_year)) as group_key,
    r.position_code as picked_position,
    e.position_code as rule_position
from season_last_rows as r
left join season_expected as e
    on
        r.team_sk = e.team_sk
        and r.player_sk = e.player_sk
        and r.league_code = e.league_code
        and r.season_api_year = e.season_api_year
where r.position_code is distinct from e.position_code

union all

select
    'int_player_momentum__metrics' as model_name,
    to_json_string(struct(m.upcoming_fixture_sk, m.team_sk, m.player_sk)) as group_key,
    m.position_code as picked_position,
    e.position_code as rule_position
from {{ ref('int_player_momentum__metrics') }} as m
left join window_expected as e
    on
        m.upcoming_fixture_sk = e.upcoming_fixture_sk
        and m.team_sk = e.team_sk
        and m.player_sk = e.player_sk
where m.position_code is distinct from e.position_code
