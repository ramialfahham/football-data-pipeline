{#
  The Player page's header and choices, recomputed here for every player, one failing row per broken case:
  an age that is not the whole years since the birth date, a full name that is not first and last name
  joined (the player name when either is missing), a featured season that another season of the player
  beats (club before national, domestic league before any other, the later year, the later last match),
  a nation whose current competitions are not those running now or, with none running, the one that
  finished last, a club tab for a player with no club match, and a national-team tab that differs from
  the player's presence on a team sheet or stat line of a current competition, or on its squad list,
  or, for a player with a page, a played match in a national edition whose last fixture is on or
  after 1 July of last season.
  A nation with a competition starting or ending within a day of the run is left out, because the
  models read the clock when they were built. A birth date on 29 February is left out of the age check,
  because a whole-year step from it lands on 28 February in a common year, and so is a birthday today,
  because the marts are built once a day and a build before midnight holds yesterday's age.
#}
{{ config(store_failures = true, severity = 'error') }}

with people as (
    select distinct
        player_sk,
        player_name,
        player_first_name,
        player_last_name,
        player_full_name,
        player_birth_date,
        player_age
    from {{ ref('mart_player_profile') }}
),

age_wrong as (
    select
        'age' as failure,
        cast(p.player_sk as string) as grain
    from people as p
    cross join unnest(generate_array(0, 130)) as n
    where
        p.player_birth_date <= current_date()
        and format_date('%m%d', p.player_birth_date) not in ('0229', format_date('%m%d', current_date()))
        and date_add(p.player_birth_date, interval n year) <= current_date()
    group by p.player_sk, p.player_age
    having p.player_age is distinct from max(n)
),

full_name_wrong as (
    select
        'full name' as failure,
        cast(player_sk as string) as grain
    from people
    where
        player_full_name is distinct from if(
            player_first_name is not null and player_last_name is not null,
            concat(player_first_name, ' ', player_last_name),
            player_name
        )
),

player_seasons as (
    select
        player_sk,
        season_sk,
        season_api_year,
        if(entity_type = 'club', 0, 1) as kind_rank,
        if(competition_type = 'domestic_league', 0, 1) as type_rank,
        max(kickoff_datetime) as last_match_at
    from {{ ref('int_legs__player_match') }}
    group by player_sk, season_sk, season_api_year, entity_type, competition_type
),

featured_beaten as (
    select
        'featured season beaten' as failure,
        concat(cast(f.player_sk as string), ' ', f.season_sk, ' by ', o.season_sk) as grain
    from {{ ref('int_player__page_profile') }} as p
    inner join player_seasons as f
        on p.player_sk = f.player_sk and p.featured_season_sk = f.season_sk
    inner join player_seasons as o
        on f.player_sk = o.player_sk and f.season_sk != o.season_sk
    where
        o.kind_rank < f.kind_rank
        or (
            o.kind_rank = f.kind_rank
            and (
                o.type_rank < f.type_rank
                or (
                    o.type_rank = f.type_rank
                    and (
                        o.season_api_year > f.season_api_year
                        or (o.season_api_year = f.season_api_year and o.last_match_at > f.last_match_at)
                    )
                )
            )
        )
),

national_seasons as (
    select
        f.season_sk,
        f.league_code,
        min(f.kickoff_datetime) as first_match_at,
        max(f.kickoff_datetime) as last_match_at
    from {{ ref('fct_fixture') }} as f
    inner join {{ ref('dim_league') }} as leagues
        on f.league_code = leagues.league_code
    where leagues.entity_type = 'national'
    group by f.season_sk, f.league_code
),

team_national_seasons as (
    select distinct
        s.season_sk,
        s.league_code,
        s.first_match_at,
        s.last_match_at,
        team_sk
    from {{ ref('fct_fixture') }} as f
    inner join national_seasons as s
        on f.season_sk = s.season_sk,
        unnest([f.home_team_sk, f.away_team_sk]) as team_sk
    where team_sk is not null
),

unsettled_teams as (
    select distinct team_sk
    from team_national_seasons
    where
        first_match_at between timestamp_sub(current_timestamp(), interval 1 day) and timestamp_add(current_timestamp(), interval 1 day)
        or last_match_at between timestamp_sub(current_timestamp(), interval 1 day) and timestamp_add(current_timestamp(), interval 1 day)
),

started as (
    select *
    from team_national_seasons
    where
        first_match_at <= current_timestamp()
        and team_sk not in (select team_sk from unsettled_teams)
),

expected_current as (
    select
        team_sk,
        season_sk
    from started
    where last_match_at >= current_timestamp()
    union all
    select
        team_sk,
        latest.season_sk
    from (
        select
            team_sk,
            array_agg(struct(season_sk) order by last_match_at desc, league_code asc, season_sk asc limit 1)[offset(0)] as latest,
            logical_or(last_match_at >= current_timestamp()) as any_running
        from started
        group by team_sk
    )
    where not any_running
),

actual_current as (
    select
        team_sk,
        season_sk
    from {{ ref('int_team__current_national_competitions') }}
    where team_sk not in (select team_sk from unsettled_teams)
),

current_wrong as (
    select
        'current competition' as failure,
        concat(cast(coalesce(e.team_sk, a.team_sk) as string), ' ', coalesce(e.season_sk, a.season_sk)) as grain
    from expected_current as e
    full outer join actual_current as a
        on e.team_sk = a.team_sk and e.season_sk = a.season_sk
    where e.team_sk is null or a.team_sk is null
),

club_players as (
    select distinct player_sk
    from {{ ref('int_legs__player_match') }}
    where entity_type = 'club'
),

club_tab_wrong as (
    select
        'club tab' as failure,
        cast(p.player_sk as string) as grain
    from {{ ref('int_player__page_profile') }} as p
    left join club_players as c
        on p.player_sk = c.player_sk
    where p.has_club_tab != (c.player_sk is not null)
),

team_sheets as (
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

expected_national as (
    select distinct s.player_sk
    from team_sheets as s
    inner join {{ ref('fct_fixture') }} as f
        on s.fixture_sk = f.fixture_sk
    inner join expected_current as c
        on s.team_sk = c.team_sk and f.season_sk = c.season_sk
    union distinct
    select distinct cast(sq.player_api_id as int64) as player_sk
    from {{ ref('base_apif__squads') }} as sq
    inner join expected_current as c
        on cast(sq.team_api_id as int64) = c.team_sk
),

edition_ends as (
    select
        season_sk,
        max(date(kickoff_datetime)) as last_match_on
    from {{ ref('fct_fixture') }}
    group by season_sk
),

expected_earned as (
    select distinct l.player_sk
    from {{ ref('int_legs__player_match') }} as l
    inner join edition_ends as e
        on l.season_sk = e.season_sk
    where
        l.entity_type != 'club'
        and l.minutes > 0
        and e.last_match_on >= date(extract(year from date_sub(current_date(), interval 6 month)) - 1, 7, 1)
),

national_tab_wrong as (
    select
        'national-team tab' as failure,
        cast(p.player_sk as string) as grain
    from {{ ref('int_player__page_profile') }} as p
    left join expected_national as e
        on p.player_sk = e.player_sk
    left join expected_earned as r
        on p.player_sk = r.player_sk
    where
        (p.national_team_sk is null or p.national_team_sk not in (select team_sk from unsettled_teams))
        and (
            p.has_national_team_tab != (e.player_sk is not null or (r.player_sk is not null and p.has_player_page))
            or p.national_tab_basis is distinct from case
                when e.player_sk is not null then 'squad'
                when r.player_sk is not null and p.has_player_page then 'earned'
            end
        )
)

select * from age_wrong
union all
select * from full_name_wrong
union all
select * from featured_beaten
union all
select * from current_wrong
union all
select * from club_tab_wrong
union all
select * from national_tab_wrong
