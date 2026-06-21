{{
    config(
        materialized='incremental',
        unique_key='event_sk',
        on_schema_change='sync_all_columns'
    )
}}

{#
    One row per match event (goals, cards, substitutions, VAR decisions) across all
    onboarded competitions. Grain: (league_code, fixture_id, event_index) — event_index
    is the zero-based array position from the API-Football /fixtures/events response.
    API-Football does not emit event IDs; array position is the only stable unique
    identifier within a fixture's event list. Once a fixture is FINISHED its event list
    does not change, so an incremental load on raw_ingested_at safely captures only new
    fixtures each run. Assist player arrives as a name only (no id in source), so it
    stays as a degenerate attribute.
#}

with base as (
    select * from {{ ref('base_apif__fixture_events') }}
),

src as (
    select *
    from base
    {% if is_incremental() %}
    -- NULL-safe high-water mark: an empty target makes max() NULL and `x > NULL` is
    -- never true, which would trap the table empty forever (see fact-not-empty test).
    -- Coalescing to the epoch lets an empty/zeroed table self-heal on the next run.
    where
        base.raw_ingested_at > (
            select coalesce(max(tgt.raw_ingested_at), timestamp('1970-01-01'))
            from {{ this }} as tgt
        )
        -- Self-heal: also re-process any fixture that currently has a null team_sk, so the
        -- base-layer team_id recovery reaches rows already committed before the fix (no
        -- --full-refresh needed). Self-limiting — once recovered they no longer match; the
        -- unique_key=event_sk merge updates the healed rows in place.
        or base.fixture_id in (
            select tgt.fixture_api_id
            from {{ this }} as tgt
            where tgt.team_sk is null
        )
    {% endif %}
)

select
    {{ dbt_utils.generate_surrogate_key(['fixture_id', 'event_index']) }} as event_sk,
    cast(fixture_id as int64) as fixture_sk,
    cast(team_id as int64) as team_sk,
    -- 0 is the API placeholder for "no player"; keep the event but null the FK so it
    -- does not point at a non-existent dim_player row (relationship tests ignore nulls).
    nullif(cast(player_id as int64), 0) as player_sk,
    league_code,
    fixture_id as fixture_api_id,
    team_id as team_api_id,
    player_id as player_api_id,
    event_index,
    minute_elapsed,
    minute_extra,
    event_type,
    event_detail,
    event_comments,
    team_name as team_name_snapshot,
    player_name as player_name_snapshot,
    assist_player_name,
    src.raw_ingested_at
from src
