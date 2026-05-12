{{ config(
    materialized='table',
    tags=['api_football', 'data_quality'],
) }}

{# One row: how aligned raw snapshot times are across D1 API-Football landing tables. #}

with per_table as (
    select
        'fixtures_next' as source_entity,
        max(ingested_at) as max_ingested_at
    from {{ source('api_football', 'raw_apif_bl1_fixtures_next') }}
    union all
    select
        'leagues' as source_entity,
        max(ingested_at) as max_ingested_at
    from {{ source('api_football', 'raw_apif_bl1_leagues') }}
    union all
    select
        'standings' as source_entity,
        max(ingested_at) as max_ingested_at
    from {{ source('api_football', 'raw_apif_bl1_standings') }}
    union all
    select
        'rounds' as source_entity,
        max(ingested_at) as max_ingested_at
    from {{ source('api_football', 'raw_apif_bl1_rounds') }}
    union all
    select
        'teams' as source_entity,
        max(ingested_at) as max_ingested_at
    from {{ source('api_football', 'raw_apif_bl1_teams') }}
    union all
    select
        'transfers' as source_entity,
        max(ingested_at) as max_ingested_at
    from {{ source('api_football', 'raw_apif_bl1_transfers') }}
    union all
    select
        'lineups' as source_entity,
        max(ingested_at) as max_ingested_at
    from {{ source('api_football', 'raw_apif_bl1_lineups') }}
    union all
    select
        'fixture_events' as source_entity,
        max(ingested_at) as max_ingested_at
    from {{ source('api_football', 'raw_apif_bl1_fixture_events') }}
    union all
    select
        'fixture_statistics' as source_entity,
        max(ingested_at) as max_ingested_at
    from {{ source('api_football', 'raw_apif_bl1_fixture_statistics') }}
    union all
    select
        'fixture_players' as source_entity,
        max(ingested_at) as max_ingested_at
    from {{ source('api_football', 'raw_apif_bl1_fixture_players') }}
    union all
    select
        'predictions' as source_entity,
        max(ingested_at) as max_ingested_at
    from {{ source('api_football', 'raw_apif_bl1_predictions') }}
    union all
    select
        'players' as source_entity,
        max(ingested_at) as max_ingested_at
    from {{ source('api_football', 'raw_apif_bl1_players') }}
)

select
    max(max_ingested_at) as latest_snapshot_at,
    min(max_ingested_at) as oldest_latest_per_table,
    timestamp_diff(
        max(max_ingested_at),
        min(max_ingested_at),
        minute
    ) as spread_minutes,
    count(*) as raw_table_count,
    countif(max_ingested_at is null) as tables_with_null_latest
from per_table
