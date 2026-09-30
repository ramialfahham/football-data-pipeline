{#
  fct_fixture_player_stats carries the cleaned columns on its history, not only on its newest rows.
  The fact is incremental: a build that adds the cleaned columns and fails before its merge leaves
  every earlier row without them, which the fact's own re-merge check repairs on the next build;
  this test fails when that did not happen. goals_penalty stands for the cleaned columns: base has
  it on every row of a match with events. A value that moved in base after its row was merged
  concerns a few rows, so the fact holding goals_penalty on fewer than half as many rows as base is
  a history that was never merged.
  Returns one row when that is the case.
#}
{{ config(store_failures = true, severity = 'error') }}

with fact_rows as (
    select countif(goals_penalty is not null) as rows_with_goals_penalty
    from {{ ref('fct_fixture_player_stats') }}
),

base_rows as (
    select countif(goals_penalty is not null) as rows_with_goals_penalty
    from {{ ref('base_apif__fixture_players') }}
)

select
    fact_rows.rows_with_goals_penalty as fact_rows_with_goals_penalty,
    base_rows.rows_with_goals_penalty as base_rows_with_goals_penalty
from fact_rows
cross join base_rows
where fact_rows.rows_with_goals_penalty * 2 < base_rows.rows_with_goals_penalty
