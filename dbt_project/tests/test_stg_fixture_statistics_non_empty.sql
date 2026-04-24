-- Fail if fixture statistics staging is empty.
select
    1 as should_fail
where (
    select count(*)
    from {{ ref('stg_apif__d1_fixture_statistics') }}
) = 0
