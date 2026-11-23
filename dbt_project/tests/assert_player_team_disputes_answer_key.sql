{#
  Hand-written stat lines and events run through player_team_disputes, the rule the base models call.
  Returns each case whose answer differs from the hand-worked one: a dispute the rule misses stays
  in the facts, and a player it catches for nothing loses his line.
#}
{{ config(store_failures = true, severity = 'error') }}

with player_rows as (
    select *
    from unnest([
        struct(1 as fixture_id, 11 as player_id, 100 as team_id),
        struct(2, 11, 100),
        struct(3, 11, 100),
        struct(4, 11, 100),
        struct(5, 11, 300),
        struct(6, 11, 100),
        struct(7, 11, 100),
        struct(8, 11, 100),
        struct(9, 11, 100),
        struct(10, 12, 100)
    ])
),

events as (
    select *
    from unnest([
        struct(
            1 as fixture_id, 11 as player_id, 200 as team_id, 'Card' as event_type,
            'Yellow Card' as event_detail, cast(null as string) as goal_correction_source,
            cast(null as string) as card_correction_source
        ),
        struct(2, 11, 100, 'Card', 'Yellow Card', cast(null as string), cast(null as string)),
        struct(3, 11, 200, 'Goal', 'Own Goal', cast(null as string), cast(null as string)),
        struct(4, 11, 300, 'Card', 'Yellow Card', cast(null as string), cast(null as string)),
        struct(5, 11, 200, 'Card', 'Yellow Card', cast(null as string), cast(null as string)),
        struct(6, 11, 200, 'Goal', 'Normal Goal', 'a source', cast(null as string)),
        struct(7, 11, 200, 'Card', 'Yellow Card', cast(null as string), 'a source'),
        struct(8, 11, 100, 'Goal', 'Normal Goal', cast(null as string), cast(null as string)),
        struct(8, 11, 200, 'Card', 'Yellow Card', cast(null as string), cast(null as string)),
        struct(9, 11, 200, 'Card', 'Yellow Card', cast(null as string), cast(null as string)),
        struct(10, 13, 200, 'Card', 'Yellow Card', cast(null as string), cast(null as string))
    ])
),

participants as (
    select *
    from unnest([
        struct(1 as fixture_id, 100 as home_team_id, 200 as away_team_id),
        struct(2, 100, 200),
        struct(3, 100, 200),
        struct(4, 100, 200),
        struct(5, 100, 200),
        struct(6, 100, 200),
        struct(7, 100, 200),
        struct(8, 100, 200),
        struct(9, 500, 600),
        struct(10, 100, 200)
    ])
),

disputes as (
    {{ player_team_disputes('player_rows', 'events', 'participants') }}
),

cases as (
    select *
    from unnest([
        struct(
            'a stat line under one team and an event under the other' as case_name,
            1 as fixture_id, 11 as player_id, true as expected
        ),
        struct('a stat line and an event under the same team', 2, 11, false),
        struct('an own goal of the other team', 3, 11, false),
        struct('an event under a team of another match', 4, 11, false),
        struct('a stat line under a team of another match', 5, 11, false),
        struct('a hand-corrected goal', 6, 11, false),
        struct('a hand-corrected card', 7, 11, false),
        struct('one event under each team', 8, 11, true),
        struct('teams that are the teams of another match', 9, 11, false),
        struct('an event of another player', 10, 12, false)
    ])
),

results as (
    select
        'player_team_disputes: ' || c.case_name as test_case,
        c.expected,
        d.fixture_id is not null as actual
    from cases as c
    left join disputes as d
        on c.fixture_id = d.fixture_id and c.player_id = d.player_id
)

select
    test_case,
    expected,
    actual
from results
where expected is distinct from actual
