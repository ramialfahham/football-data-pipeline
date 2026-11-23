{#
  Hand-written matches run through score_stopped_at_90, the rule the checked fixtures model calls.
  Returns each case whose answer differs from the hand-worked one: a score that stopped at 90
  minutes and is not caught is shown, and a score caught for nothing is withheld.
#}
{{ config(store_failures = true, severity = 'error') }}

with cases as (
    select *
    from unnest([
        struct(
            'the score is the first 90 minutes and an open-play goal follows' as case_name,
            1 as goals_home, 1 as goals_away, 1 as home_goals_in_90, 1 as away_goals_in_90,
            1 as open_play_goals_after_90, 0 as goals_without_minute, true as expected
        ),
        struct('the score counts the extra-time goal', 2, 1, 1, 1, 1, 0, false),
        struct('no goal comes after minute 90', 1, 1, 1, 1, 0, 0, false),
        struct('a goal has no minute', 1, 1, 1, 1, 1, 1, false),
        struct('only the home side adds up', 1, 2, 1, 1, 1, 0, false),
        struct('only the away side adds up', 2, 1, 1, 1, 1, 0, false),
        struct('the score is withheld already', cast(null as int64), cast(null as int64), 1, 1, 1, 0, false)
    ])
),

results as (
    select
        'score_stopped_at_90: ' || case_name as test_case,
        expected,
        {{ score_stopped_at_90(
            'goals_home', 'goals_away', 'home_goals_in_90', 'away_goals_in_90',
            'open_play_goals_after_90', 'goals_without_minute'
        ) }} as actual
    from cases
)

select
    test_case,
    expected,
    actual
from results
where expected is distinct from actual
