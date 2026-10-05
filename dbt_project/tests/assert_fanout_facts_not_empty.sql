-- An empty fanout fact silently blanks every downstream surface; all three are rebuilt in full
-- from base every night. This test fails loudly if any of them is empty.
{{ config(severity = 'error', store_failures = true) }}

with counts as (
    select 'fct_fixture_player_stats' as model_name, count(*) as row_count
    from {{ ref('fct_fixture_player_stats') }}
    union all
    select 'fct_fixture_team_stats' as model_name, count(*) as row_count
    from {{ ref('fct_fixture_team_stats') }}
    union all
    select 'fct_fixture_event' as model_name, count(*) as row_count
    from {{ ref('fct_fixture_event') }}
)

select
    model_name,
    row_count
from counts
where row_count = 0
