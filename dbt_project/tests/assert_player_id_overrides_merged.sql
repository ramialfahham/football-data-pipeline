-- A merged player has one page and one set of stats: the wrong id is gone everywhere, the id kept
-- holds the matches of both, and no fetch lists both ids in one match, where one row would be lost.
with overrides as (
    select
        wrong_player_api_id,
        correct_player_api_id
    from {{ ref('player_id_overrides') }}
),

left_behind as (
    select
        'dim_player' as found_in,
        player_sk as player_id
    from {{ ref('dim_player') }}
    union all
    select
        'mart_player_profile',
        player_sk
    from {{ ref('mart_player_profile') }}
    union all
    select
        'fct_fixture_player_stats',
        player_sk
    from {{ ref('fct_fixture_player_stats') }}
    union all
    select
        'fct_fixture_lineup',
        player_sk
    from {{ ref('fct_fixture_lineup') }}
    union all
    select
        'fct_fixture_event',
        player_sk
    from {{ ref('fct_fixture_event') }}
    union all
    select
        'fct_fixture_event assist',
        assist_player_sk
    from {{ ref('fct_fixture_event') }}
),

provider_matches as (
    select
        overrides.correct_player_api_id as player_id,
        count(distinct stat_rows.fixture_id) as matches
    from overrides
    inner join {{ ref('stg_apif__fixture_players') }} as stat_rows
        on stat_rows.player_id in (overrides.wrong_player_api_id, overrides.correct_player_api_id)
    group by overrides.correct_player_api_id
),

both_ids_in_one_fetch as (
    select overrides.correct_player_api_id as player_id
    from overrides
    inner join {{ ref('stg_apif__fixture_players') }} as stat_rows
        on stat_rows.player_id in (overrides.wrong_player_api_id, overrides.correct_player_api_id)
    group by overrides.correct_player_api_id, stat_rows.fixture_id, stat_rows.raw_ingested_at
    having count(distinct stat_rows.player_id) > 1
),

merged_matches as (
    select
        player_id,
        count(distinct fixture_id) as matches
    from {{ ref('base_apif__fixture_players') }}
    group by player_id
)

select
    left_behind.found_in,
    left_behind.player_id,
    0 as expected_matches,
    0 as merged_matches
from left_behind
inner join overrides
    on left_behind.player_id = overrides.wrong_player_api_id

union all

select
    'matches not summed' as found_in,
    provider_matches.player_id,
    provider_matches.matches as expected_matches,
    coalesce(merged_matches.matches, 0) as merged_matches
from provider_matches
left join merged_matches
    on provider_matches.player_id = merged_matches.player_id
where provider_matches.matches != coalesce(merged_matches.matches, 0)

union all

select
    'both ids in one fetch' as found_in,
    both_ids_in_one_fetch.player_id,
    0 as expected_matches,
    0 as merged_matches
from both_ids_in_one_fetch
