-- Fail if fixture statistics staging is empty.
select
    1
    as should_fail
from (
    select
        count(*)
        as row_count
    from {{ ref('stg_apif__d1_fixture_statistics') }}
) as check_rows
where check_rows.row_count = 0
