with src as (
    -- INCREMENTAL accumulation: the /players/profiles loader is skip-if-present, so each
    -- ingestion snapshot holds only that run's NEW players. We therefore UNION ALL snapshots
    -- (no `partition by league_code` latest-snapshot select — that would silently drop players
    -- landed on earlier backfill days). Faithful 1:1 flatten only; no entity dedup here — base
    -- assembles current-per-player. See dbt_project/docs/layering.md §1_staging + the
    -- incremental-accumulation note in stg_apif__generic.yml.
    select *
    from {{ source('api_football', 'raw_apif_player_profiles') }}
),

profile_blocks as (
    select
        src.ingested_at as raw_ingested_at,
        src.league_code,
        player_block,
        safe_cast(json_value(player_block, '$.player_id') as int64) as player_id
    from src,
        unnest(json_query_array(json_query(src.payload, '$.response'), '$')) as player_block
),

profile_rows as (
    select
        league_code,
        raw_ingested_at,
        player_id,
        profile_el
    from profile_blocks,
        unnest(json_query_array(json_query(player_block, '$.profile_payload'), '$')) as profile_el
)

select
    league_code,
    raw_ingested_at,
    player_id,
    json_value(profile_el, '$.player.name') as player_name,
    json_value(profile_el, '$.player.firstname') as player_firstname,
    json_value(profile_el, '$.player.lastname') as player_lastname,
    safe_cast(json_value(profile_el, '$.player.age') as int64) as age,
    safe_cast(json_value(profile_el, '$.player.birth.date') as date) as birth_date,
    json_value(profile_el, '$.player.birth.place') as birth_place,
    json_value(profile_el, '$.player.birth.country') as birth_country,
    json_value(profile_el, '$.player.nationality') as nationality,
    json_value(profile_el, '$.player.height') as height,
    json_value(profile_el, '$.player.weight') as weight,
    safe_cast(json_value(profile_el, '$.player.number') as int64) as squad_number,
    json_value(profile_el, '$.player.position') as position,
    json_value(profile_el, '$.player.photo') as player_photo_url
from profile_rows
