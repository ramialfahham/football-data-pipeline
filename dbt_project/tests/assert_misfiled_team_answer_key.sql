{#
  Hand-written lines run through team_not_in_fixture, the rule the base models and the tests call.
  Returns each case whose answer differs from the hand-worked one: a misfiled line the rule misses
  stays in the facts, and a line it catches for nothing leaves them.
#}
{{ config(store_failures = true, severity = 'error') }}

with cases as (
    select *
    from unnest([
        struct(
            'a team that did not play' as case_name,
            5 as team_id, 1 as home_team_id, 2 as away_team_id, true as expected
        ),
        struct('the home team', 1, 1, 2, false),
        struct('the away team', 2, 1, 2, false),
        struct('a line with no team', cast(null as int64), 1, 2, false),
        struct('a match with an unknown home team', 5, cast(null as int64), 2, false),
        struct('a match with an unknown away team', 5, 1, cast(null as int64), false)
    ])
),

results as (
    select
        'team_not_in_fixture: ' || case_name as test_case,
        expected,
        {{ team_not_in_fixture('team_id', 'home_team_id', 'away_team_id') }} as actual
    from cases
)

select
    test_case,
    expected,
    actual
from results
where expected is distinct from actual
