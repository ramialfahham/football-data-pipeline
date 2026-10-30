{#
  Every version of a league's tie-break rules carries one provider_order_differs value, so
  assert_team_table_equals_published_tables leaves out a version's level places entirely or not at
  all. One row per version with both values.
#}
{{ config(severity = 'error') }}

select
    league_code,
    from_season,
    phase,
    count(distinct provider_order_differs) as values_held
from {{ ref('league_tiebreak_rules') }}
group by league_code, from_season, phase
having count(distinct provider_order_differs) != 1
