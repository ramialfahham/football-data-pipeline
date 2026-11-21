{#
  The Player page's comparison blocks, recomputed here for every player and squad, one failing row per
  broken case: a competition in the Club or National team filter that is not in its place (domestic league
  first, then the later last match of the competition, then the code), a Squad whose count is not the
  players who reached a third of the team's minutes, a Squad rank that is not one more than the players
  with a higher value, a Squad median that is not the middle of its values, and a Club tab whose minutes
  this season or last season are not the player's minutes in the competitions of the window.
#}
{{ config(store_failures = true, severity = 'error') }}

with shown_competitions as (
    select distinct
        b.player_sk,
        b.season_sk,
        b.league_code,
        b.page_tab,
        b.competition_order,
        w.competition_type,
        w.last_match_at
    from {{ ref('mart_player_competition_benchmarks') }} as b
    inner join {{ ref('int_player_page__window_seasons') }} as w
        on
            b.player_sk = w.player_sk
            and b.season_sk = w.season_sk
            and w.window_type = if(b.page_tab = 'club', 'this_season', 'current_competitions')
    where b.page_tab is not null
),

filter_order_wrong as (
    select
        'filter order' as failure,
        concat(cast(player_sk as string), ' ', page_tab, ' ', season_sk) as grain
    from (
        select
            *,
            row_number() over (
                partition by player_sk, page_tab
                order by
                    case competition_type
                        when 'domestic_league' then 1
                        when 'domestic_cup' then 2
                        when 'domestic_super_cup' then 3
                        else 4
                    end asc,
                    last_match_at desc,
                    league_code asc,
                    season_sk asc
            ) as expected_order
        from shown_competitions
    )
    where competition_order != expected_order
),

squad_rows as (
    select
        squad_sk,
        player_sk,
        metric_key,
        metric_value,
        squad_player_count,
        squad_median,
        rank
    from {{ ref('mart_player_squad_benchmarks') }}
),

squad_members as (
    select
        squad_sk,
        count(*) as members
    from {{ ref('int_player_squad_window__metrics') }}
    where minutes >= team_matches * 90 / 3 and not stats_need_research
    group by squad_sk
),

squad_count_wrong as (
    select
        'squad count' as failure,
        r.squad_sk as grain
    from (
        select
            squad_sk,
            min(squad_player_count) as lowest,
            max(squad_player_count) as highest
        from squad_rows
        group by squad_sk
    ) as r
    left join squad_members as m
        on r.squad_sk = m.squad_sk
    where r.lowest != r.highest or r.highest is distinct from m.members
),

squad_rank_wrong as (
    select
        'squad rank' as failure,
        concat(s.squad_sk, ' ', s.metric_key, ' ', cast(s.player_sk as string)) as grain
    from squad_rows as s
    inner join squad_rows as o
        on s.squad_sk = o.squad_sk and s.metric_key = o.metric_key
    group by s.squad_sk, s.metric_key, s.player_sk, s.rank
    having s.rank != 1 + countif(o.metric_value > s.metric_value)
),

squad_median_wrong as (
    select
        'squad median' as failure,
        concat(squad_sk, ' ', metric_key) as grain
    from (
        select
            squad_sk,
            metric_key,
            squad_median,
            metric_value,
            row_number() over (partition by squad_sk, metric_key order by metric_value asc) as position_in_order,
            count(*) over (partition by squad_sk, metric_key) as values_counted
        from squad_rows
    )
    where position_in_order in (div(values_counted + 1, 2), div(values_counted, 2) + 1)
    group by squad_sk, metric_key, squad_median
    having squad_median is null or abs(avg(metric_value) - squad_median) > 1e-9
),

window_minutes as (
    select
        p.player_sk,
        w.window_type,
        sum(l.minutes) as minutes
    from {{ ref('int_player__page_profile') }} as p
    inner join {{ ref('int_competition_season__club_windows') }} as w
        on p.featured_season_sk = w.anchor_season_sk
    inner join {{ ref('int_legs__player_match') }} as l
        on p.player_sk = l.player_sk and w.season_sk = l.season_sk
    group by p.player_sk, w.window_type
),

club_tabs as (
    select distinct
        player_sk,
        minutes,
        minutes_prev_season
    from {{ ref('mart_player_window_metrics') }}
    where page_tab = 'club'
),

tab_minutes_wrong as (
    select
        'club tab minutes' as failure,
        cast(t.player_sk as string) as grain
    from club_tabs as t
    left join window_minutes as this_season
        on t.player_sk = this_season.player_sk and this_season.window_type = 'this_season'
    left join window_minutes as last_season
        on t.player_sk = last_season.player_sk and last_season.window_type = 'last_season'
    where
        (t.minutes is not null and t.minutes is distinct from this_season.minutes)
        or (t.minutes_prev_season is not null and t.minutes_prev_season is distinct from last_season.minutes)
)

select * from filter_order_wrong
union all
select * from squad_count_wrong
union all
select * from squad_rank_wrong
union all
select * from squad_median_wrong
union all
select * from tab_minutes_wrong
