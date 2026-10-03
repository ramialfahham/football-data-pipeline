{#
  fct_fixture_team_stats carries the cleaned columns on its history, not only on its newest rows.
  The fact is incremental: a build that adds the cleaned columns and fails before its merge leaves
  every earlier row without them, which the fact's own re-merge check repairs on the next build;
  this test fails when that did not happen. shots stands for the cleaned columns: base has it on
  nearly every team-match with a stat line. A value that moved in base after its row was merged
  concerns a few rows, so the fact holding shots on fewer than half as many rows as base is a history
  that was never merged.
  Returns one row when that is the case.
#}
{{ config(store_failures = true, severity = 'error') }}

with fact_rows as (
    select countif(shots is not null) as rows_with_shots
    from {{ ref('fct_fixture_team_stats') }}
),

base_rows as (
    select countif(shots is not null) as rows_with_shots
    from {{ ref('base_apif__fixture_statistics') }}
)

select
    fact_rows.rows_with_shots as fact_rows_with_shots,
    base_rows.rows_with_shots as base_rows_with_shots
from fact_rows
cross join base_rows
where fact_rows.rows_with_shots * 2 < base_rows.rows_with_shots
