{#
  The rule for who gets a Player page, one failing row per broken case: has_player_page differs from
  a count of the player's matches in mart_player_fixture_stats and the player's tabs, differs between
  a player's rows, or differs from the known players, each worked by hand from their match lines.
#}
{{ config(store_failures = true, severity = 'error') }}

with current_seasons as (
    select
        extract(year from date_sub(current_date(), interval 6 month)) as split_year_season,
        extract(year from current_date()) as calendar_year_season
),

matches_played as (
    select
        s.player_sk,
        count(*) as matches
    from {{ ref('mart_player_fixture_stats') }} as s
    cross join current_seasons as c
    left join {{ ref('competition_season_map') }} as m
        on s.league_code = m.league_code and s.season_api_year = m.season_api_year
    where
        s.minutes_played > 0
        and case
            when s.page_tab = 'national_team' then date(s.kickoff_datetime) >= date(c.split_year_season - 1, 7, 1)
            when m.season_type = 'split_year' then m.split_year_season >= c.split_year_season - 1
            else m.calendar_year_season >= c.calendar_year_season - 1
        end
    group by s.player_sk
),

profiles as (
    select
        player_sk,
        logical_or(has_player_page) as has_player_page,
        logical_and(has_player_page) as has_player_page_on_every_row
    from {{ ref('mart_player_profile') }}
    group by player_sk
),

known_players as (
    select *
    from unnest([
        struct(184 as player_sk, true as has_player_page, 'Harry Kane, every match of 2025-26 at Bayern.' as working),
        (1155, true, 'Kevin Kampl: 3 Bundesliga matches in 2025-26, the last on 27 September 2025.'),
        (2822, false, 'Darko Lazović: 2 AFC Champions League matches, the last on 22 December 2025.'),
        (332, false, 'Dries Mertens: 364 matches, the last on 30 May 2025, before last season.'),
        (309763, true, 'Livano Comenencia: 13 Curaçao matches, and no club match in our data.')
    ])
),

count_differs as (
    select
        'has_player_page differs from the count and the tabs' as failure,
        cast(p.player_sk as string) as grain
    from profiles as p
    inner join {{ ref('int_player__page_profile') }} as t
        on p.player_sk = t.player_sk
    left join matches_played as m
        on p.player_sk = m.player_sk
    where p.has_player_page != (coalesce(m.matches, 0) >= 3 and (t.has_club_tab or t.has_national_team_tab))
),

rows_differ as (
    select
        'has_player_page differs between the rows of a player' as failure,
        cast(player_sk as string) as grain
    from profiles
    where has_player_page != has_player_page_on_every_row
),

known_player_differs as (
    select
        'known player' as failure,
        k.working as grain
    from known_players as k
    left join profiles as p
        on k.player_sk = p.player_sk
    where p.has_player_page is distinct from k.has_player_page and current_date() < date '2027-07-01'
)

select * from count_differs
union all
select * from rows_differ
union all
select * from known_player_differs
