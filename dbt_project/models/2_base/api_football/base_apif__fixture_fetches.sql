{#
  Each fixture's latest fetch of its fixture-details bundle: the newest raw_ingested_at over its
  player stats, line-ups, events and statistics, so a fetch whose player stats came back empty
  still counts. A fixture whose latest fetch came under 72 hours after kickoff waits for its
  second fetch (docs/data_contract.md, "Second fetch"), the ingestion's
  coverage.second_fetch_due rule: its player stats are not final yet.
  Grain: fixture_id.
#}

with fetches as (
    select
        fixture_id,
        raw_ingested_at
    from {{ ref('stg_apif__fixture_players') }}
    union all
    select
        fixture_id,
        raw_ingested_at
    from {{ ref('stg_apif__lineups') }}
    union all
    select
        fixture_id,
        raw_ingested_at
    from {{ ref('stg_apif__fixture_events') }}
    union all
    select
        fixture_id,
        raw_ingested_at
    from {{ ref('stg_apif__fixture_statistics') }}
),

latest_fetches as (
    select
        fixture_id,
        max(raw_ingested_at) as latest_fetch_at
    from fetches
    where fixture_id is not null
    group by fixture_id
)

select
    l.fixture_id,
    l.latest_fetch_at,
    coalesce(
        l.latest_fetch_at < timestamp_add(f.kickoff_datetime, interval 72 hour), false
    ) as is_awaiting_second_fetch
from latest_fetches as l
left join {{ ref('base_apif__fixtures_next') }} as f
    on l.fixture_id = f.fixture_id
