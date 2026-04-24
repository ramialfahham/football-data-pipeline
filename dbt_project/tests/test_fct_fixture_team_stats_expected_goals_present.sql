-- Fail if core fixture team stats has zero non-null expected_goals.
select
    1
    as should_fail
from (
    select
        count(*)
        as xg_non_null_rows
    from {{ ref('fct_fixture_team_stats') }}
    where expected_goals is not null
) as check_rows
where check_rows.xg_non_null_rows = 0
