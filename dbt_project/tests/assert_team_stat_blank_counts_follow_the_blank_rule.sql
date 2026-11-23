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

participants as (
    select
        fixture_api_id as fixture_id,
        home_team_api_id as home_team_id,
        away_team_api_id as away_team_id
    from {{ ref('fct_fixture') }}
),

-- A player whose stat line and events name the two teams of the match has no line in the fact, and
-- his offsides still keep his team's blank count blank in base.
disputed_players as (
    select distinct
        r.fixture_id,
        r.player_id
    from {{ ref('base_apif__fixture_players') }} as r
    inner join {{ ref('base_apif__fixture_events') }} as e
        on r.fixture_id = e.fixture_id and r.player_id = e.player_id
    inner join participants as p
        on r.fixture_id = p.fixture_id
    where
        e.team_id != r.team_id
        and r.team_id in (p.home_team_id, p.away_team_id)
        and e.team_id in (p.home_team_id, p.away_team_id)
        and not (e.event_type = 'Goal' and e.event_detail = 'Own Goal')
        and e.goal_correction_source is null
        and e.card_correction_source is null
),

players_with_an_offside as (
    select
        fixture_sk,
        team_sk
    from {{ ref('fct_fixture_player_stats') }}
    where offsides > 0
    group by fixture_sk, team_sk
    union distinct
    select
        r.fixture_id as fixture_sk,
        r.team_id as team_sk
    from {{ ref('base_apif__fixture_players') }} as r
    inner join disputed_players as d
        on r.fixture_id = d.fixture_id and r.player_id = d.player_id
    where r.offsides > 0
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
