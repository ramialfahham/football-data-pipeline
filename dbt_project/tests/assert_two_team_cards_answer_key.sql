{#
  Hand-written card events run through card_events_naming_two_teams, the rule the models and the
  research list call. Returns each case whose answer differs from the hand-worked one: a two-team
  player the rule misses keeps his cards, and a player it catches for nothing loses them.
#}
{{ config(store_failures = true, severity = 'error') }}

with card_events as (
    select *
    from unnest([
        struct(
            1 as fixture_id, 7 as player_id, 10 as team_id, 'Card' as event_type,
            cast(null as string) as event_comments, true as has_full_events
        ),
        struct(1, 7, 20, 'Card', cast(null as string), true),
        struct(1, 8, 10, 'Card', cast(null as string), true),
        struct(1, 8, 10, 'Card', cast(null as string), true),
        struct(2, 7, 10, 'Card', cast(null as string), true),
        struct(2, 7, 20, 'Card', 'Not on pitch', true),
        struct(3, 7, 10, 'Card', cast(null as string), false),
        struct(3, 7, 20, 'Card', cast(null as string), false),
        struct(4, 7, 10, 'Goal', cast(null as string), true),
        struct(4, 7, 20, 'Card', cast(null as string), true),
        struct(5, cast(null as int64), 10, 'Card', cast(null as string), true),
        struct(5, cast(null as int64), 20, 'Card', cast(null as string), true)
    ])
),

two_team_players as (
    {{ card_events_naming_two_teams('card_events') }}
),

cases as (
    select *
    from unnest([
        struct('two teams in one match' as case_name, 1 as fixture_id, 7 as player_id, true as expected),
        struct('two cards of one team', 1, 8, false),
        struct('a coach card of the other team is no player card', 2, 7, false),
        struct('a match without full events', 3, 7, false),
        struct('a goal of one team and a card of the other', 4, 7, false),
        struct('cards of both teams that name no player', 5, cast(null as int64), false)
    ])
),

results as (
    select
        c.expected,
        'card_events_naming_two_teams: ' || c.case_name as test_case,
        t.fixture_id is not null as actual
    from cases as c
    left join two_team_players as t
        on c.fixture_id = t.fixture_id and c.player_id is not distinct from t.player_id
)

select
    test_case,
    expected,
    actual
from results
where expected is distinct from actual
