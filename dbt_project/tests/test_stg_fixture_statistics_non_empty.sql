-- Fail if fixture statistics staging is empty.
{{ config(store_failures = true) }}

select
    1
    as should_fail
from (
    select
        count(*)
        as row_count
    from {{ ref('stg_apif__fixture_statistics') }}
) as check_rows
where check_rows.row_count = 0
