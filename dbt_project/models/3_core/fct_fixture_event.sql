{{ config(materialized='table') }}

{#
    One row per match event (goals, cards, substitutions, VAR decisions).
    The source grain uses minute_elapsed + minute_extra + player + type + detail
    as disambiguators; the surrogate key hashes that exact tuple so we can
    assert uniqueness. Assist player arrives as a name only (no id in source),
    so it stays as a degenerate attribute.
#}

with import_base_apif__bl1_fixture_events as (
    select * from {{ ref('base_apif__bl1_fixture_events') }}
)

select
    {{ dbt_utils.generate_surrogate_key([
        'fixture_id',
        'minute_elapsed',
        'minute_extra',
        'team_id',
        'player_id',
        'event_type',
        'event_detail'
    ]) }} as event_sk,
    cast(fixture_id as int64) as fixture_sk,
    cast(team_id as int64) as team_sk,
    cast(player_id as int64) as player_sk,
    league_code,
    fixture_id as fixture_api_id,
    team_id as team_api_id,
    player_id as player_api_id,
    minute_elapsed,
    minute_extra,
    event_type,
    event_detail,
    event_comments,
    team_name as team_name_snapshot,
    player_name as player_name_snapshot,
    assist_player_name,
    raw_ingested_at
from import_base_apif__bl1_fixture_events
