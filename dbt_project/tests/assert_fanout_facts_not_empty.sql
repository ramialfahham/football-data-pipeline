-- Guards the incremental high-water-mark trap. The fanout facts load only rows newer
-- than max(raw_ingested_at) of the target; on an EMPTY target that max is NULL and
-- `raw_ingested_at > NULL` is never true, so an emptied table can never repopulate and
-- silently blanks every downstream surface. fct_fixture_player_stats sat empty (0 rows)
-- this way while its base had ~800k rows. The models now coalesce the max to the epoch so
-- an empty table self-heals; this test fails loudly if any fanout fact is empty regardless.
{{ config(severity = 'error') }}

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
