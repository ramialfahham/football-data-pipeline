-- A club the provider holds under two ids is one team: the duplicate id is gone everywhere, the id
-- kept holds the matches of both, and no match or standings table names both ids, where folding
-- would make a club play itself or drop one of two rows.
{{ config(store_failures = true) }}

with overrides as (
    select
        cast(wrong_team_api_id as int64) as wrong_team_api_id,
        cast(correct_team_api_id as int64) as correct_team_api_id
    from {{ ref('fixture_team_id_overrides') }}
    where mode = 'alias'
),

in_fixture_rows as (
    select distinct cast(fixture_id as int64) as fixture_id
    from {{ ref('fixture_team_id_overrides') }}
    where mode = 'reattribute_in_fixture'
),

left_behind as (
    select
        'dim_team' as found_in,
        team_sk as team_id
    from {{ ref('dim_team') }}
    union all
    select
        'fct_fixture home' as found_in,
        home_team_sk as team_id
    from {{ ref('fct_fixture') }}
    union all
    select
        'fct_fixture away' as found_in,
        away_team_sk as team_id
    from {{ ref('fct_fixture') }}
    union all
    select
        'fct_standings' as found_in,
        team_sk as team_id
    from {{ ref('fct_standings') }}
    union all
    select
        'fct_fixture_lineup' as found_in,
        team_sk as team_id
    from {{ ref('fct_fixture_lineup') }}
    union all
    select
        'fct_fixture_event' as found_in,
        team_sk as team_id
    from {{ ref('fct_fixture_event') }}
    union all
    select
        'fct_fixture_player_stats' as found_in,
        team_sk as team_id
    from {{ ref('fct_fixture_player_stats') }}
    union all
    select
        'fct_fixture_team_stats' as found_in,
        team_sk as team_id
    from {{ ref('fct_fixture_team_stats') }}
    union all
    select
        'dim_team_competition_season_mapping' as found_in,
        team_sk as team_id
    from {{ ref('dim_team_competition_season_mapping') }}
    union all
    select
        'dim_player_team_season_mapping' as found_in,
        team_sk as team_id
    from {{ ref('dim_player_team_season_mapping') }}
    union all
    select
        'dim_coach_team_mapping' as found_in,
        team_sk as team_id
    from {{ ref('dim_coach_team_mapping') }}
    union all
    select
        'fct_transfer in' as found_in,
        team_in_sk as team_id
    from {{ ref('fct_transfer') }}
    union all
    select
        'fct_transfer out' as found_in,
        team_out_sk as team_id
    from {{ ref('fct_transfer') }}
),

provider_fixtures as (
    select
        fixture_id,
        home_team_id,
        away_team_id
    from {{ ref('stg_apif__fixtures_next') }}
    where
        fixture_id is not null
        and fixture_id not in (select in_fixture_rows.fixture_id from in_fixture_rows)
    qualify row_number() over (partition by fixture_id order by raw_ingested_at desc) = 1
),

provider_matches as (
    select
        overrides.correct_team_api_id as team_id,
        count(distinct provider_fixtures.fixture_id) as matches
    from overrides
    inner join provider_fixtures
        on
            overrides.wrong_team_api_id in (provider_fixtures.home_team_id, provider_fixtures.away_team_id)
            or overrides.correct_team_api_id in (provider_fixtures.home_team_id, provider_fixtures.away_team_id)
    group by overrides.correct_team_api_id
),

merged_matches as (
    select
        overrides.correct_team_api_id as team_id,
        count(distinct fixtures.fixture_id) as matches
    from overrides
    inner join {{ ref('base_apif__fixtures_next') }} as fixtures
        on overrides.correct_team_api_id in (fixtures.home_team_id, fixtures.away_team_id)
    where fixtures.fixture_id not in (select in_fixture_rows.fixture_id from in_fixture_rows)
    group by overrides.correct_team_api_id
),

both_ids_in_one_fixture as (
    select overrides.correct_team_api_id as team_id
    from overrides
    inner join {{ ref('stg_apif__fixtures_next') }} as fixtures
        on
            (
                overrides.wrong_team_api_id = fixtures.home_team_id
                and overrides.correct_team_api_id = fixtures.away_team_id
            )
            or (
                overrides.correct_team_api_id = fixtures.home_team_id
                and overrides.wrong_team_api_id = fixtures.away_team_id
            )
),

both_ids_in_one_table as (
    select overrides.correct_team_api_id as team_id
    from overrides
    inner join {{ ref('stg_apif__standings') }} as standings
        on
            overrides.wrong_team_api_id = standings.team_id
            or overrides.correct_team_api_id = standings.team_id
    group by overrides.correct_team_api_id, standings.league_code, standings.season, standings.group_name
    having count(distinct standings.team_id) > 1
),

chained as (
    select first_override.correct_team_api_id as team_id
    from overrides as first_override
    inner join overrides as second_override
        on first_override.correct_team_api_id = second_override.wrong_team_api_id
)

select
    left_behind.found_in,
    left_behind.team_id,
    0 as expected_matches,
    0 as merged_matches
from left_behind
inner join overrides
    on left_behind.team_id = overrides.wrong_team_api_id

union all

select
    'matches not summed' as found_in,
    provider_matches.team_id,
    provider_matches.matches as expected_matches,
    coalesce(merged_matches.matches, 0) as merged_matches
from provider_matches
left join merged_matches
    on provider_matches.team_id = merged_matches.team_id
where provider_matches.matches != coalesce(merged_matches.matches, 0)

union all

select
    'both ids in one fixture' as found_in,
    team_id,
    0 as expected_matches,
    0 as merged_matches
from both_ids_in_one_fixture

union all

select
    'both ids in one standings table' as found_in,
    team_id,
    0 as expected_matches,
    0 as merged_matches
from both_ids_in_one_table

union all

select
    'kept id is itself a duplicate' as found_in,
    team_id,
    0 as expected_matches,
    0 as merged_matches
from chained
