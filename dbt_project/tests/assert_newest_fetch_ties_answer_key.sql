{#
  Hand-written rows run through newest_fetch_ties, the rule that finds a tie and says whether it
  differs. Returns each key whose answer differs from the hand-worked one: a differing tie reported
  as identical lets one of two different rows stand for the key, and an identical tie reported as
  differing withholds a value nothing is wrong with. Only the newest ingest time of a key counts. A
  column we add to a row (load_offset) and the id the provider filed a team under (provider_team_id)
  never make identical content differ.
#}
{{ config(store_failures = true, severity = 'error') }}

with sheet_rows as (
    select *
    from unnest([
        struct(
            1 as fixture_id, 10 as team_id, 2 as raw_ingested_at, 'a' as sheet, 1 as load_offset,
            10 as provider_team_id
        ),
        struct(1, 10, 2, 'a', 1, 10),
        struct(2, 10, 2, 'a', 1, 10),
        struct(2, 10, 2, 'b', 1, 10),
        struct(3, 10, 2, 'a', 1, 10),
        struct(4, 10, 1, 'a', 1, 10),
        struct(4, 10, 1, 'b', 1, 10),
        struct(4, 10, 2, 'a', 1, 10),
        struct(5, 10, 1, 'a', 1, 10),
        struct(5, 10, 2, 'a', 1, 10),
        struct(5, 10, 2, 'b', 1, 10),
        struct(6, 10, 2, 'a', 1, 10),
        struct(6, 10, 2, 'a', 1, 10),
        struct(6, 11, 2, 'a', 1, 11),
        struct(6, 11, 2, 'b', 1, 11),
        struct(7, 10, 2, 'a', 1, 10),
        struct(7, 10, 2, 'a', 1, 10),
        struct(7, 10, 2, 'a', 1, 10),
        struct(8, 10, 3, 'a', 1, 10),
        struct(8, 11, 2, 'a', 1, 11),
        struct(8, 11, 2, 'b', 1, 11),
        struct(9, 10, 2, 'a', 1, 10),
        struct(9, 10, 2, 'a', 2, 10),
        struct(10, 10, 2, 'a', 1, 10),
        struct(10, 10, 2, 'b', 2, 10),
        struct(11, 10, 2, 'a', 1, 100),
        struct(11, 10, 2, 'a', 1, 101),
        struct(12, 10, 2, 'a', 1, 100),
        struct(12, 10, 2, 'b', 1, 101)
    ])
),

actual as (
    {{ newest_fetch_ties('sheet_rows', ['fixture_id', 'team_id'], ['load_offset', 'provider_team_id']) }}
),

expected as (
    select *
    from unnest([
        struct(1 as fixture_id, 10 as team_id, 2 as tied_rows, false as rows_differ),
        struct(2, 10, 2, true),
        struct(3, 10, 1, false),
        struct(4, 10, 1, false),
        struct(5, 10, 2, true),
        struct(6, 10, 2, false),
        struct(6, 11, 2, true),
        struct(7, 10, 3, false),
        struct(8, 10, 1, false),
        struct(8, 11, 2, true),
        struct(9, 10, 2, false),
        struct(10, 10, 2, true),
        struct(11, 10, 2, false),
        struct(12, 10, 2, true)
    ])
)

select
    'wrong_answer' as problem,
    coalesce(e.fixture_id, a.fixture_id) as fixture_id,
    coalesce(e.team_id, a.team_id) as team_id,
    e.tied_rows as expected_tied_rows,
    a.tied_rows as actual_tied_rows,
    e.rows_differ as expected_rows_differ,
    a.rows_differ as actual_rows_differ
from expected as e
full outer join actual as a
    on e.fixture_id = a.fixture_id and e.team_id = a.team_id
where
    e.fixture_id is null
    or a.fixture_id is null
    or e.tied_rows != a.tied_rows
    or e.rows_differ != a.rows_differ
