{#
  The competition-seasons of each window on a player's page. this_season and last_season are the
  club competitions around the player's featured season, at any club; current_competitions are the
  player's nation's. competition_type and last_match_at carry what the page's competition order
  needs. Grain: (player_sk, window_type, season_sk).
#}

with profile as (
    select * from {{ ref('int_player__page_profile') }}
),

season_ends as (
    select
        season_sk,
        league_code,
        max(kickoff_datetime) as last_match_at
    from {{ ref('fct_fixture') }}
    group by season_sk, league_code
),

windows as (
    select
        p.player_sk,
        w.window_type,
        w.season_sk,
        cast(null as int64) as team_sk
    from profile as p
    inner join {{ ref('int_competition_season__club_windows') }} as w
        on p.featured_season_sk = w.anchor_season_sk
    union all
    select
        p.player_sk,
        'current_competitions' as window_type,
        c.season_sk,
        c.team_sk
    from profile as p
    inner join {{ ref('int_team__current_national_competitions') }} as c
        on p.national_team_sk = c.team_sk
)

select
    w.player_sk,
    w.window_type,
    w.season_sk,
    w.team_sk,
    e.league_code,
    reg.competition_type,
    e.last_match_at
from windows as w
inner join season_ends as e
    on w.season_sk = e.season_sk
inner join {{ ref('dim_league') }} as reg
    on e.league_code = reg.league_code
