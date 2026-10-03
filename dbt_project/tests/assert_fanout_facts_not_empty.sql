-- An empty fanout fact silently blanks every downstream surface. fct_fixture_event loads only
-- rows newer than max(raw_ingested_at) of the target, which on an EMPTY target is NULL, so it
-- coalesces that max to the epoch to self-heal; the two stat facts are rebuilt in full from base.
-- This test fails loudly if any fanout fact is empty regardless.
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
