{#
  A nation's current competitions. A national-team competition is current from its first match to
  its last, for every nation in it, whether or not that nation is still playing. A nation with none
  running keeps the one that finished most recently. window_is_complete is false when any of them
  holds a team match of the nation with no player data (rule R4).

  Grain: (team_sk, season_sk).
#}

with seasons as (
    select
        f.season_sk,
        f.league_code,
        f.season_api_year,
        min(f.kickoff_datetime) as first_match_at,
        max(f.kickoff_datetime) as last_match_at
    from {{ ref('fct_fixture') }} as f
    inner join {{ ref('dim_league') }} as leagues
        on f.league_code = leagues.league_code
    where leagues.entity_type = 'national'
    group by f.season_sk, f.league_code, f.season_api_year
),

team_seasons as (
    select distinct
        f.season_sk,
        team_sk
    from {{ ref('fct_fixture') }} as f,
        unnest([f.home_team_sk, f.away_team_sk]) as team_sk
    where team_sk is not null
),

started as (
    select
        ts.team_sk,
        s.season_sk,
        s.league_code,
        s.season_api_year,
        s.first_match_at,
        s.last_match_at,
        current_timestamp() <= s.last_match_at as is_running
    from team_seasons as ts
    inner join seasons as s
        on ts.season_sk = s.season_sk
    where s.first_match_at <= current_timestamp()
),

current_competitions as (
    select *
    from started
    qualify
        is_running
        or (
            not logical_or(is_running) over (partition by team_sk)
            and row_number() over (partition by team_sk order by last_match_at desc, league_code asc) = 1
        )
),

without_player_data as (
    {{ team_seasons_without_player_data() }}
)

select
    c.team_sk,
    c.season_sk,
    c.league_code,
    c.season_api_year,
    c.first_match_at,
    c.last_match_at,
    c.is_running,
    logical_and(u.team_sk is null) over (partition by c.team_sk) as window_is_complete
from current_competitions as c
left join without_player_data as u
    on c.team_sk = u.team_sk and c.season_sk = u.season_sk
