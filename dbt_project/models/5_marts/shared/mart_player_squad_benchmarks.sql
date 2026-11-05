{#
  The Squad comparison of the Player page, in long form: every player of a squad who played at least
  a third of the team's minutes in the window (team matches x 90 / 3), goalkeepers included, on each
  outfield metric, with the rank from the most to the least, the median and the squad's count. A
  squad reads as a player's role, not quality, so rank ignores the metric's direction.

  has_squad_filter marks the row of a player whose page shows this squad: their own team and
  window, reached the floor, and an outfield player. A squad with a team match with no player data has
  blank minutes (rule R4 in models/docs/metric_rules.md), so it holds nobody.

  Grain: (squad_sk, player_sk, metric_key).
#}

with squad as (
    select * from {{ ref('int_player_squad_window__metrics') }}
    where minutes >= team_matches * 90 / 3
),

profile as (
    select * from {{ ref('int_player__page_profile') }}
),

metrics as (
    select
        s.squad_sk,
        s.page_tab,
        s.team_sk,
        s.anchor_season_sk,
        s.player_sk,
        s.minutes,
        m.metric_key,
        m.metric_value
    from squad as s,
        unnest({{ player_benchmark_metrics('s', with_floors=false) }}) as m
    where 'ATT' in unnest(m.position_groups) and m.metric_value is not null
),

squad_size as (
    select
        squad_sk,
        count(*) as squad_player_count
    from squad
    group by squad_sk
)

select
    m.squad_sk,
    m.page_tab,
    m.team_sk,
    m.anchor_season_sk,
    m.player_sk,
    m.minutes,
    m.metric_key,
    m.metric_value,
    n.squad_player_count,
    percentile_cont(m.metric_value, 0.5) over (partition by m.squad_sk, m.metric_key) as squad_median,
    rank() over (partition by m.squad_sk, m.metric_key order by m.metric_value desc) as rank,
    coalesce(p.position_group, '') != 'GK'
    and (
        (m.page_tab = 'club' and m.team_sk = p.featured_team_sk and m.anchor_season_sk = p.featured_season_sk)
        or (m.page_tab = 'national_team' and m.team_sk = p.national_team_sk and p.has_national_team_tab)
    ) as has_squad_filter
from metrics as m
inner join squad_size as n
    on m.squad_sk = n.squad_sk
left join profile as p
    on m.player_sk = p.player_sk
