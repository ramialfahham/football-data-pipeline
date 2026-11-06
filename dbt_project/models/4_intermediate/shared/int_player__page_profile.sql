{#
  One row per player: the choices the Player page opens on, each made here so nothing downstream
  ranks them.

  featured_season_sk is the most recent club season, a domestic league before a cup; a player with no
  club football falls back to the most recent season of any kind. Two competitions of the same kind
  in one year go to the one with the latest match. position_group is the player's most frequent
  position that season. current_club_team_sk is the club of the player's latest club match;
  featured_team_sk the club of the latest match in the featured season's club competitions.

  has_national_team_tab is true for a player in a nation's squad for a current competition: named on
  a team sheet or a stat line of one of its matches, or on the provider's squad list for it.
  national_team_sk is that nation, the one of the latest match when there are two.

  has_player_page reads a club match's season from competition_season_map, by its competition's
  season type. A national-team competition has no placing there, so its matches count from the
  start of last split-year season.

  Grain: (player_sk).
#}

with legs as (
    select * from {{ ref('int_legs__player_match') }}
),

seasons as (
    select
        player_sk,
        season_sk,
        league_code,
        season_api_year,
        competition_type,
        entity_type,
        max(kickoff_datetime) as last_match_at
    from legs
    group by player_sk, season_sk, league_code, season_api_year, competition_type, entity_type
),

featured as (
    select
        player_sk,
        season_sk as featured_season_sk,
        entity_type as featured_entity_type
    from seasons
    qualify row_number() over (
        partition by player_sk
        order by
            case when entity_type = 'club' then 0 else 1 end asc,
            case when competition_type = 'domestic_league' then 0 else 1 end asc,
            season_api_year desc,
            last_match_at desc,
            league_code asc
    ) = 1
),

featured_position as (
    select
        l.player_sk,
        case l.position_code
            when 'G' then 'GK'
            when 'D' then 'DEF'
            when 'M' then 'MID'
            when 'F' then 'ATT'
        end as position_group
    from legs as l
    inner join featured as fe
        on l.player_sk = fe.player_sk and l.season_sk = fe.featured_season_sk
    where l.position_code in ('G', 'D', 'M', 'F')
    group by l.player_sk, l.position_code
    qualify row_number() over (
        partition by l.player_sk
        order by count(*) desc, l.position_code asc
    ) = 1
),

current_club as (
    select
        player_sk,
        team_sk as current_club_team_sk
    from legs
    where entity_type = 'club'
    qualify row_number() over (
        partition by player_sk
        order by kickoff_datetime desc, fixture_sk desc
    ) = 1
),

featured_team as (
    select
        l.player_sk,
        l.team_sk as featured_team_sk
    from legs as l
    inner join featured as fe
        on l.player_sk = fe.player_sk
    inner join {{ ref('int_competition_season__club_windows') }} as w
        on
            fe.featured_season_sk = w.anchor_season_sk
            and l.season_sk = w.season_sk
            and w.window_type = 'this_season'
    qualify row_number() over (
        partition by l.player_sk
        order by l.kickoff_datetime desc, l.fixture_sk desc
    ) = 1
),

current_national as (
    select * from {{ ref('int_team__current_national_competitions') }}
),

fixtures as (
    select
        fixture_sk,
        season_sk,
        kickoff_datetime
    from {{ ref('fct_fixture') }}
),

sheets as (
    select
        fixture_sk,
        team_sk,
        player_sk
    from {{ ref('fct_fixture_lineup') }}
    where lineup_state in ('confirmed', 'researched') and player_sk is not null
    union distinct
    select
        fixture_sk,
        team_sk,
        player_sk
    from {{ ref('fct_fixture_player_stats') }}
),

squad_members as (
    select
        s.player_sk,
        s.team_sk,
        f.kickoff_datetime as named_at
    from sheets as s
    inner join fixtures as f
        on s.fixture_sk = f.fixture_sk
    inner join current_national as c
        on s.team_sk = c.team_sk and f.season_sk = c.season_sk
    union all
    select
        cast(sq.player_api_id as int64) as player_sk,
        cast(sq.team_api_id as int64) as team_sk,
        cast(null as timestamp) as named_at
    from {{ ref('base_apif__squads') }} as sq
    inner join current_national as c
        on cast(sq.team_api_id as int64) = c.team_sk and sq.league_code = c.league_code
),

national_team as (
    select
        player_sk,
        team_sk as national_team_sk
    from squad_members
    qualify row_number() over (
        partition by player_sk
        order by named_at desc nulls last, team_sk asc
    ) = 1
),

current_seasons as (
    select
        extract(year from date_sub(current_date(), interval 6 month)) as split_year_season,
        extract(year from current_date()) as calendar_year_season
),

players_with_a_page as (
    select l.player_sk
    from legs as l
    cross join current_seasons as c
    left join {{ ref('dim_competition_season') }} as d
        on l.season_sk = d.season_sk
    where
        l.minutes > 0
        and if(
            l.entity_type = 'club',
            if(
                d.season_type = 'split_year',
                d.split_year_season >= c.split_year_season - 1,
                d.calendar_year_season >= c.calendar_year_season - 1
            ),
            date(l.kickoff_datetime) >= date(c.split_year_season - 1, 7, 1)
        )
    group by l.player_sk
    having count(*) >= 3
)

select
    fe.player_sk,
    fe.featured_season_sk,
    fe.featured_entity_type,
    fp.position_group,
    cc.current_club_team_sk,
    ft.featured_team_sk,
    nt.national_team_sk,
    nt.player_sk is not null as has_national_team_tab,
    cc.player_sk is not null as has_club_tab,
    pp.player_sk is not null and (nt.player_sk is not null or cc.player_sk is not null) as has_player_page
from featured as fe
left join featured_position as fp
    on fe.player_sk = fp.player_sk
left join current_club as cc
    on fe.player_sk = cc.player_sk
left join featured_team as ft
    on fe.player_sk = ft.player_sk
left join national_team as nt
    on fe.player_sk = nt.player_sk
left join players_with_a_page as pp
    on fe.player_sk = pp.player_sk
