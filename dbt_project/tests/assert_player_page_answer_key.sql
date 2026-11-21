{#
  Hand-worked Player page values (seeds/player_page_answer_key.csv): real players and squads in seasons
  that are over, each answer worked out from the cleaned player-match lines, the team matches and the
  fixtures, never from a Player page mart. The marts must return exactly the expected value, or a blank
  where the key is blank. A number compares at 1e-9. Returns each case whose value differs and each
  case whose row is missing from the mart.
#}
{{ config(store_failures = true, severity = 'error') }}

with answer_key as (
    select * from {{ ref('player_page_answer_key') }}
),

header as (
    select
        'header' as block,
        p.player_sk as player_id,
        'featured' as scope,
        f.field,
        f.actual_text
    from {{ ref('mart_player_profile') }} as p,
        unnest([
            struct('full_name' as field, p.player_full_name as actual_text),
            ('season_label', p.season_label),
            ('league_code', p.league_code),
            ('current_club_name', p.current_club_name),
            ('position_group', p.position_group),
            ('has_club_tab', cast(p.has_club_tab as string)),
            ('has_national_team_tab', cast(p.has_national_team_tab as string))
        ]) as f
    where p.is_featured_season
),

position_counts as (
    select distinct
        'position_count' as block,
        cast(null as int64) as player_id,
        concat(league_code, '|', season_api_year, '|', position_group) as scope,
        'position_player_count' as field,
        cast(position_player_count as string) as actual_text
    from {{ ref('mart_player_competition_benchmarks') }}
),

filter_order as (
    select distinct
        'competition_order' as block,
        player_sk as player_id,
        concat(league_code, '|', season_api_year) as scope,
        'competition_order' as field,
        cast(competition_order as string) as actual_text
    from {{ ref('mart_player_competition_benchmarks') }}
    where page_tab is not null
),

club_window as (
    select
        'club_window' as block,
        w.player_sk as player_id,
        w.metric_key as scope,
        f.field,
        f.actual_text
    from {{ ref('mart_player_window_metrics') }} as w,
        unnest([
            struct('value' as field, cast(w.metric_value as string) as actual_text),
            ('minutes', cast(w.minutes as string)),
            ('minutes_prev_season', cast(w.minutes_prev_season as string))
        ]) as f
    where w.page_tab = 'club'
),

squad as (
    select distinct
        'squad' as block,
        cast(null as int64) as player_id,
        squad_sk as scope,
        'squad_player_count' as field,
        cast(squad_player_count as string) as actual_text
    from {{ ref('mart_player_squad_benchmarks') }}
    union distinct
    select distinct
        'squad' as block,
        cast(null as int64) as player_id,
        squad_sk as scope,
        concat(metric_key, '.squad_median') as field,
        cast(squad_median as string) as actual_text
    from {{ ref('mart_player_squad_benchmarks') }}
    union distinct
    select distinct
        'squad' as block,
        player_sk as player_id,
        squad_sk as scope,
        concat(metric_key, '.rank') as field,
        cast(rank as string) as actual_text
    from {{ ref('mart_player_squad_benchmarks') }}
),

actual as (
    select
        *,
        safe_cast(actual_text as float64) as actual_number
    from (
        select * from header
        union all
        select * from position_counts
        union all
        select * from filter_order
        union all
        select * from club_window
        union all
        select * from squad
    )
)

select
    k.block,
    k.player_id,
    k.scope,
    k.field,
    k.expected,
    a.actual_text,
    a.block is not null as row_found
from answer_key as k
left join actual as a
    on
        k.block = a.block
        and k.scope = a.scope
        and k.field = a.field
        and k.player_id is not distinct from a.player_id
where
    a.block is null
    or case
        when k.expected is null then a.actual_text is not null
        when safe_cast(k.expected as float64) is not null and a.actual_number is not null
            then abs(safe_cast(k.expected as float64) - a.actual_number) > 1e-9
        else k.expected is distinct from a.actual_text
    end
