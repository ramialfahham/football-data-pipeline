-- A team's blank offsides count is a zero when its own line has fouls and possession and no player
-- of it has an offside (the cleaning_rules Blank rule), and stays blank otherwise. Returns a row
-- (= fails) for a full line with a blank offsides count and no player with an offside, and for a
-- thin line whose offsides is 0 when the other
-- team's line is thin too and blank, which the clause must not produce. A full line here has fouls
-- above 0, because the table's fouls is the cleaned count, which is 0 where the other team's
-- line has fouls and the own count is blank.
{{ config(store_failures = true) }}

with lines as (
    select
        fixture_sk,
        team_sk,
        has_stat_line,
        offsides,
        coalesce(fouls > 0, false) and possession_pct is not null as is_full_line
    from {{ ref('fct_fixture_team_stats') }}
),

players_with_an_offside as (
    select
        fixture_sk,
        team_sk
    from {{ ref('fct_fixture_player_stats') }}
    where offsides > 0
    group by fixture_sk, team_sk
),

full_line_blanks as (
    select
        l.fixture_sk,
        l.team_sk,
        'full line with a blank offsides count and no player with an offside' as failure
    from lines as l
    left join players_with_an_offside as p
        on l.fixture_sk = p.fixture_sk and l.team_sk = p.team_sk
    where
        l.has_stat_line
        and l.is_full_line
        and l.offsides is null
        and p.fixture_sk is null
),

thin_line_zeros as (
    select
        l.fixture_sk,
        l.team_sk,
        'thin line with offsides 0 and no value on the other team line' as failure
    from lines as l
    inner join lines as o
        on l.fixture_sk = o.fixture_sk and l.team_sk != o.team_sk
    where
        l.has_stat_line
        and not l.is_full_line
        and l.offsides = 0
        and not o.is_full_line
        and o.offsides is null
)

select * from full_line_blanks
union all
select * from thin_line_zeros
