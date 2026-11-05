{#
  What a Player page shows for a whole tab, in long form: the four cards, and on the Club tab each
  metric of the player's position this season against last season. The Club tab's window is the club
  competitions of the featured season at any club; the National team tab's is the nation's current
  competitions. metric_value_prev_season is the same metric over the whole of last season. A blank
  value is rule R4 in models/docs/metric_rules.md.

  A squad member with no match in the National team window has the cards at 0 and the rates blank.
  saves_player_pct is a goalkeeper's card and a comparison row at once.

  Grain: (player_sk, page_tab, metric_key).
#}

with profile as (
    select * from {{ ref('int_player__page_profile') }}
),

windows as (
    select * from {{ ref('int_player_window__metrics') }}
),

nation_windows as (
    select distinct
        team_sk,
        window_is_complete
    from {{ ref('int_team__current_national_competitions') }}
),

tabs as (
    select
        player_sk,
        'club' as page_tab,
        'this_season' as window_type,
        position_group,
        featured_team_sk as team_sk,
        false as unused_counts_as_zero
    from profile
    where featured_entity_type = 'club'
    union all
    select
        p.player_sk,
        'national_team' as page_tab,
        'current_competitions' as window_type,
        p.position_group,
        p.national_team_sk as team_sk,
        n.window_is_complete as unused_counts_as_zero
    from profile as p
    inner join nation_windows as n
        on p.national_team_sk = n.team_sk
    where p.has_national_team_tab
),

tab_windows as (
    select
        w.* except (player_sk, window_type),
        t.page_tab,
        t.position_group,
        t.team_sk,
        t.player_sk as tab_player_sk,
        w.player_sk is null and t.unused_counts_as_zero as is_unused_squad_member
    from tabs as t
    left join windows as w
        on t.player_sk = w.player_sk and t.window_type = w.window_type
),

cards as (
    select
        t.tab_player_sk as player_sk,
        t.page_tab,
        m.metric_key,
        if(t.is_unused_squad_member, m.unused_value, m.metric_value) as metric_value,
        true as is_card,
        false as is_comparison
    from tab_windows as t,
        unnest([
            struct(
                'appearances' as metric_key,
                'all' as shown_for,
                cast(t.appearances as float64) as metric_value,
                cast(0 as float64) as unused_value
            ),
            ('minutes_per_appearance', 'all', t.minutes_per_appearance, null),
            ('goals_player', 'outfield', cast(t.goals_player as float64), 0),
            ('assists_player', 'outfield', cast(t.assists_player as float64), 0),
            ('saves_player_pct', 'goalkeeper', t.saves_player_pct, null),
            ('goals_against_player', 'goalkeeper', cast(t.goals_against_player as float64), 0)
        ]) as m
    where
        m.shown_for = 'all'
        or m.shown_for = if(t.position_group = 'GK', 'goalkeeper', 'outfield')
),

comparison as (
    select
        t.tab_player_sk as player_sk,
        t.page_tab,
        m.metric_key,
        m.metric_value,
        false as is_card,
        true as is_comparison
    from tab_windows as t,
        unnest({{ player_benchmark_metrics('t', with_floors=false) }}) as m
    where t.page_tab = 'club' and t.position_group in unnest(m.position_groups)
),

last_season as (
    select
        w.player_sk,
        m.metric_key,
        m.metric_value
    from windows as w,
        unnest({{ player_benchmark_metrics('w', with_floors=false) }}) as m
    where w.window_type = 'last_season'
),

last_season_minutes as (
    select
        player_sk,
        minutes
    from windows
    where window_type = 'last_season'
),

all_rows as (
    select * from cards
    union all
    select * from comparison
),

rows_shown as (
    select
        player_sk,
        page_tab,
        metric_key,
        any_value(metric_value) as metric_value,
        logical_or(is_card) as is_card,
        logical_or(is_comparison) as is_comparison
    from all_rows
    group by player_sk, page_tab, metric_key
)

select
    r.player_sk,
    r.page_tab,
    t.team_sk,
    r.metric_key,
    r.is_card,
    r.is_comparison,
    t.minutes,
    if(r.page_tab = 'club', lm.minutes, null) as minutes_prev_season,
    r.metric_value,
    if(r.page_tab = 'club' and r.is_comparison, l.metric_value, null) as metric_value_prev_season
from rows_shown as r
inner join tab_windows as t
    on r.player_sk = t.tab_player_sk and r.page_tab = t.page_tab
left join last_season as l
    on r.player_sk = l.player_sk and r.metric_key = l.metric_key
left join last_season_minutes as lm
    on r.player_sk = lm.player_sk
