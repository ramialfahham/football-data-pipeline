{#
  The rule for who gets a Player page, one failing row per broken case: has_player_page differs from
  a count of the player's matches in mart_player_fixture_stats, differs between a player's rows, or
  differs from the known players, each worked by hand from their match lines; a known player whose
  National team tab is missing; and a player with a page who has no tab. A national-team match counts when its edition's last fixture is on or after
  1 July of last season.
#}
{{ config(store_failures = true, severity = 'error') }}

with current_seasons as (
    select
        extract(year from date_sub(current_date(), interval 6 month)) as split_year_season,
        extract(year from current_date()) as calendar_year_season
),

edition_ends as (
    select
        season_sk,
        max(date(kickoff_datetime)) as last_match_on
    from {{ ref('fct_fixture') }}
    group by season_sk
),

matches_played as (
    select
        s.player_sk,
        count(*) as matches
    from {{ ref('mart_player_fixture_stats') }} as s
    cross join current_seasons as c
    inner join {{ ref('fct_fixture') }} as f
        on s.fixture_sk = f.fixture_sk
    left join edition_ends as e
        on f.season_sk = e.season_sk
    left join {{ ref('competition_season_map') }} as m
        on s.league_code = m.league_code and s.season_api_year = m.season_api_year
    where
        s.minutes_played > 0
        and case
            when s.page_tab = 'national_team' then e.last_match_on >= date(c.split_year_season - 1, 7, 1)
            when m.season_type = 'split_year' then m.split_year_season >= c.split_year_season - 1
            else m.calendar_year_season >= c.calendar_year_season - 1
        end
    group by s.player_sk
),

profiles as (
    select
        player_sk,
        logical_or(has_player_page) as has_player_page,
        logical_and(has_player_page) as has_player_page_on_every_row,
        logical_or(has_national_team_tab) as has_national_team_tab
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
        (309763, true, 'Livano Comenencia: 13 Curaçao matches, and no club match in our data.'),
        (213937, true, 'Luis Santamaría (Honduras): 5 Gold Cup 2025 matches, last one on 6 July 2025, no club match.'),
        (108650, true, 'S. Ortiz (El Salvador): 1 Gold Cup and 2 World Cup qualifiers in 2025, no club match.'),
        (108669, false, 'K. Santamaría (El Salvador): 1 World Cup qualifier in 2025.')
    ])
),

known_national_tabs as (
    select *
    from unnest([
        struct(213937 as player_sk, 'Luis Santamaría: a page from Gold Cup 2025 only, in no current squad.' as working),
        (108650, 'S. Ortiz: a page from Gold Cup 2025 and 2025 qualifiers only, in no current squad.')
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
    where p.has_player_page != (coalesce(m.matches, 0) >= 3)
),

page_without_tab as (
    select
        'player with a page and no tab' as failure,
        cast(p.player_sk as string) as grain
    from profiles as p
    inner join {{ ref('int_player__page_profile') }} as t
        on p.player_sk = t.player_sk
    where p.has_player_page and not (t.has_club_tab or t.has_national_team_tab)
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
),

known_national_tab_differs as (
    select
        'known national-team tab' as failure,
        k.working as grain
    from known_national_tabs as k
    left join profiles as p
        on k.player_sk = p.player_sk
    where p.has_national_team_tab is distinct from true and current_date() < date '2027-07-01'
)

select * from count_differs
union all
select * from page_without_tab
union all
select * from rows_differ
union all
select * from known_player_differs
union all
select * from known_national_tab_differs
