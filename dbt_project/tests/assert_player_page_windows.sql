{#
  The rules of the Player page's windows and choices, one failing row per broken case:
  a competition-season in both this and last season of one anchor, so a match would count twice;
  a nation with no current competition though one has started;
  a player whose featured season is not one of the seasons the player played;
  a lower_better benchmark whose rank_best_first 1 is not its lowest value;
  a squad row under the floor of a third of the team's minutes;
  a tab whose played matches differ from its Appearances card.
#}
{{ config(store_failures = true, severity = 'error') }}

with double_counted as (
    select
        'season in both windows' as failure,
        t.anchor_season_sk as grain
    from {{ ref('int_competition_season__club_windows') }} as t
    inner join {{ ref('int_competition_season__club_windows') }} as l
        on t.anchor_season_sk = l.anchor_season_sk and t.season_sk = l.season_sk
    where t.window_type = 'this_season' and l.window_type = 'last_season'
),

nations_with_a_started_competition as (
    select distinct team_sk
    from {{ ref('fct_fixture') }} as f,
        unnest([f.home_team_sk, f.away_team_sk]) as team_sk
    inner join {{ ref('competition_registry') }} as reg
        on f.league_code = reg.league_code
    inner join {{ ref('competition_types') }} as typ
        on reg.competition_type = typ.competition_type
    where
        typ.entity_type = 'national'
        and team_sk is not null
        and f.kickoff_datetime <= current_timestamp()
),

nation_without_current as (
    select
        'nation with no current competition' as failure,
        cast(n.team_sk as string) as grain
    from nations_with_a_started_competition as n
    left join {{ ref('int_team__current_national_competitions') }} as c
        on n.team_sk = c.team_sk
    where c.team_sk is null
),

featured_not_played as (
    select
        'featured season not played' as failure,
        cast(p.player_sk as string) as grain
    from {{ ref('int_player__page_profile') }} as p
    left join {{ ref('int_player_season__metrics') }} as s
        on p.player_sk = s.player_sk and p.featured_season_sk = s.season_sk
    where s.player_sk is null
),

lower_better_ranks as (
    select
        'lower_better rank 1 is not the lowest' as failure,
        concat(b.league_code, ' ', b.season_api_year, ' ', b.position_group, ' ', b.metric_key) as grain
    from {{ ref('mart_player_competition_benchmarks') }} as b
    inner join {{ ref('metric_catalogue') }} as c
        on b.metric_key = c.metric_id and c.entity = 'player'
    where c.direction = 'lower_better'
    group by b.league_code, b.season_api_year, b.position_group, b.metric_key
    having min(if(b.rank_best_first = 1, b.metric_value, null)) != min(b.metric_value)
),

squad_under_floor as (
    select
        'squad player under the floor' as failure,
        concat(b.squad_sk, ' ', b.player_sk) as grain
    from {{ ref('mart_player_squad_benchmarks') }} as b
    inner join {{ ref('int_player_squad_window__metrics') }} as s
        on b.squad_sk = s.squad_sk and b.player_sk = s.player_sk
    where s.minutes * 3 < s.team_matches * 90
),

played_in_window as (
    select
        player_sk,
        page_tab,
        countif(match_involvement = 'played') as played
    from {{ ref('mart_player_fixture_stats') }}
    where is_in_page_window
    group by player_sk, page_tab
),

played_differs_from_card as (
    select
        'played matches differ from the Appearances card' as failure,
        concat(cast(w.player_sk as string), ' ', w.page_tab) as grain
    from {{ ref('mart_player_window_metrics') }} as w
    left join played_in_window as m
        on w.player_sk = m.player_sk and w.page_tab = m.page_tab
    where
        w.metric_key = 'appearances'
        and w.metric_value != coalesce(m.played, 0)
)

select * from double_counted
union all
select * from nation_without_current
union all
select * from featured_not_played
union all
select * from lower_better_ranks
union all
select * from squad_under_floor
union all
select * from played_differs_from_card
