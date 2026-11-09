{#
  A cross-group ranking is a ranking and a real table never is. WC 2026 "Group Stage" and ACN 2027
  "Groups" hold one team from each group, so they are rankings, and every other section of those
  two league-seasons stays a group. No section of a split-season league (BPL, VL, KL1, LMX, APD)
  is a ranking, though each of its teams sits in two tables. Each failing row is a section whose
  kind breaks one of these.
#}
{{ config(store_failures = true, severity = 'error') }}

with kinds as (
    select * from {{ ref('int_standings__section_kinds') }}
),

rankings as (
    select
        'WC' as league_code,
        2026 as season_api_year,
        'Group Stage' as group_name
    union all
    select
        'ACN' as league_code,
        2027 as season_api_year,
        'Groups' as group_name
),

ranking_seasons as (
    select distinct
        league_code,
        season_api_year
    from rankings
)

select
    r.league_code,
    r.season_api_year,
    r.group_name,
    k.table_kind,
    'a cross-group ranking' as expected
from rankings as r
left join kinds as k
    on
        r.league_code = k.league_code
        and r.season_api_year = k.season_api_year
        and r.group_name = k.group_name
where k.table_kind is distinct from 'ranking'

union all

select
    k.league_code,
    k.season_api_year,
    k.group_name,
    k.table_kind,
    'a group' as expected
from kinds as k
inner join ranking_seasons as s
    on k.league_code = s.league_code and k.season_api_year = s.season_api_year
left join rankings as r
    on
        k.league_code = r.league_code
        and k.season_api_year = r.season_api_year
        and k.group_name = r.group_name
where r.group_name is null and k.table_kind != 'group'

union all

select
    league_code,
    season_api_year,
    group_name,
    table_kind,
    'never a ranking in a split season' as expected
from kinds
where league_code in ('BPL', 'VL', 'KL1', 'LMX', 'APD') and table_kind = 'ranking'
