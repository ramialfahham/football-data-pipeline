-- Fail if core fixture team stats has zero non-null expected_goals.
select
    1 as should_fail
where (
    select count(*)
    from {{ ref('fct_fixture_team_stats') }}
    where expected_goals is not null
) = 0
