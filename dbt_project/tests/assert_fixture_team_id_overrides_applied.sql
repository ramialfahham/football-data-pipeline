-- Every reattribute_in_fixture row of fixture_team_id_overrides is applied. One row per broken row:
--   - wrong_id_still_carried: the fixture list or a match feed still files the fixture under the
--     wrong team id, named in model_name.
--   - correct_id_missing: the fixture list has no such fixture, or neither of its teams is the
--     correct id.

{{ config(store_failures = true, severity = 'error') }}

with overrides as (
    select
        cast(fixture_id as int64) as fixture_id,
        cast(wrong_team_api_id as int64) as wrong_team_api_id,
        cast(correct_team_api_id as int64) as correct_team_api_id
    from {{ ref('fixture_team_id_overrides') }}
    where mode = 'reattribute_in_fixture'
),

fixtures as (
    select
        fixture_id,
        home_team_id,
        away_team_id
    from {{ ref('base_apif__fixtures_next') }}
),

carried_teams as (
    select
        'base_apif__fixtures_next' as model_name,
        fixture_id,
        home_team_id as team_id
    from fixtures
    union all
    select
        'base_apif__fixtures_next' as model_name,
        fixture_id,
        away_team_id as team_id
    from fixtures
    union all
    select
        'base_apif__fixture_events' as model_name,
        fixture_id,
        team_id
    from {{ ref('base_apif__fixture_events') }}
    union all
    select
        'base_apif__fixture_players' as model_name,
        fixture_id,
        team_id
    from {{ ref('base_apif__fixture_players') }}
    union all
    select
        'base_apif__fixture_statistics' as model_name,
        fixture_id,
        team_id
    from {{ ref('base_apif__fixture_statistics') }}
    union all
    select
        'base_apif__lineups' as model_name,
        fixture_id,
        team_id
    from {{ ref('base_apif__lineups') }}
)

select distinct
    o.fixture_id,
    o.wrong_team_api_id,
    o.correct_team_api_id,
    t.model_name,
    'wrong_id_still_carried' as problem
from overrides as o
inner join carried_teams as t
    on
        o.fixture_id = t.fixture_id
        and o.wrong_team_api_id = t.team_id
union all
select
    o.fixture_id,
    o.wrong_team_api_id,
    o.correct_team_api_id,
    'base_apif__fixtures_next' as model_name,
    'correct_id_missing' as problem
from overrides as o
left join fixtures as f
    on o.fixture_id = f.fixture_id
where
    f.fixture_id is null
    or (
        f.home_team_id is distinct from o.correct_team_api_id
        and f.away_team_id is distinct from o.correct_team_api_id
    )
