{#
  Every version of a league's tie-break rules ends at undecidable, so teams still level after its
  last computable criterion have no place in int_team_season__table_by_time. One row per version
  whose last criterion is something else, or that holds undecidable before its end.
#}
{{ config(severity = 'error') }}

with versions as (
    select
        league_code,
        from_season,
        phase,
        max(criterion_order) as last_order,
        max_by(criterion, criterion_order) as last_criterion,
        countif(criterion = 'undecidable') as undecidable_rows
    from {{ ref('league_tiebreak_rules') }}
    group by league_code, from_season, phase
)

select *
from versions
where last_criterion != 'undecidable' or undecidable_rows != 1
