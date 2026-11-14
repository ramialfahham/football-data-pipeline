{#
  A midfielder is compared within his season role: every benchmark row in DM, CM or AM is the player's
  own season midfield_role, a MID row belongs to a player without one, and no player has rows in two
  midfield pools of one competition-season. A role row of a player whose page position is MID is
  placed on his page exactly like a MID row would be. Returns the rows that break this.
#}

with benchmark_rows as (
    select distinct
        player_sk,
        season_sk,
        position_group,
        page_tab
    from {{ ref('mart_player_competition_benchmarks') }}
    where position_group in ('DM', 'CM', 'AM', 'MID')
),

roles as (
    select
        player_sk,
        season_sk,
        midfield_role
    from {{ ref('int_player_season__metrics') }}
),

wrong_pool as (
    select
        b.player_sk,
        b.season_sk,
        b.position_group,
        'pool is not the season role' as problem
    from benchmark_rows as b
    left join roles as r
        on b.player_sk = r.player_sk and b.season_sk = r.season_sk
    where b.position_group != coalesce(r.midfield_role, 'MID')
),

two_pools as (
    select
        player_sk,
        season_sk,
        string_agg(distinct position_group) as position_group,
        'two midfield pools' as problem
    from benchmark_rows
    group by player_sk, season_sk
    having count(distinct position_group) > 1
),

page_windows as (
    select
        w.player_sk,
        w.season_sk
    from {{ ref('int_player_page__window_seasons') }} as w
    inner join {{ ref('int_player__page_profile') }} as p
        on w.player_sk = p.player_sk
    where w.window_type in ('this_season', 'current_competitions') and p.position_group = 'MID'
),

off_the_page as (
    select
        b.player_sk,
        b.season_sk,
        b.position_group,
        'midfield row of a page window without a page tab' as problem
    from benchmark_rows as b
    inner join page_windows as w
        on b.player_sk = w.player_sk and b.season_sk = w.season_sk
    where b.page_tab is null
)

select * from wrong_pool
union all
select * from two_pools
union all
select * from off_the_page
