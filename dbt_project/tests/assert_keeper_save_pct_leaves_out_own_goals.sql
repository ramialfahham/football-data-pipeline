{{ config(severity = 'error', store_failures = true) }}

-- A keeper's save percentage leaves out the own goals conceded while he was in goal. Three real
-- matches with an own goal conceded: Chelsea's two keepers who shared fixture 868079 (both own goals
-- in the first half, before the change at 46), and the whole-match keepers of Hoffenheim in 1575150
-- and Union Berlin in 1575216. Fails a keeper whose goals conceded, own goals conceded or match save
-- percentage differs from the value read from the match's events.

with expected as (
    select * from unnest([
        struct(868079 as fixture_sk, 2273 as player_sk, 1 as saves, 3 as goals_against, 2 as goals_own_against),
        struct(868079, 2986, 4, 1, 0),
        struct(1575150, 702, 2, 3, 1),
        struct(1575216, 1798, 8, 2, 1)
    ])
),

actual as (
    select
        fixture_sk,
        player_sk,
        saves,
        goals_against,
        goals_own_against
    from {{ ref('int_legs__player_match') }}
    where fixture_sk in (868079, 1575150, 1575216)
)

select
    e.fixture_sk,
    e.player_sk,
    e.saves as expected_saves,
    a.saves,
    e.goals_against as expected_goals_against,
    a.goals_against,
    e.goals_own_against as expected_goals_own_against,
    a.goals_own_against,
    safe_divide(e.saves, e.saves + e.goals_against - e.goals_own_against) as expected_save_pct,
    safe_divide(a.saves, a.saves + a.goals_against - a.goals_own_against) as save_pct
from expected as e
left join actual as a
    on e.fixture_sk = a.fixture_sk and e.player_sk = a.player_sk
where
    a.player_sk is null
    or a.saves is distinct from e.saves
    or a.goals_against is distinct from e.goals_against
    or a.goals_own_against is distinct from e.goals_own_against
