with src as (
    -- ACCUMULATION: a fetch writes only the teams it fetched (an in-season comp every run, a
    -- finished comp's teams once), so no row is a complete snapshot of its league and the newest
    -- row per league_code would drop every team it does not carry. All rows are read; base picks
    -- the newest block of each team. See dbt_project/docs/layering.md §1_staging.
    select *
    from {{ source('api_football', 'raw_apif_squads') }}
),

team_blocks as (
    select
        src.ingested_at as raw_ingested_at,
        src.league_code,
        team_block,
        safe_cast(json_value(team_block, '$.team_id') as int64) as team_id
    from src,
        unnest(json_query_array(json_query(src.payload, '$.response'), '$')) as team_block
),

-- The left joins keep a team block whose list is empty as one row with no player, so base can see
-- that a newer fetch found the squad empty and not fall back to an older list.
player_rows as (
    select
        team_blocks.league_code,
        team_blocks.raw_ingested_at,
        team_blocks.team_id,
        player_el
    from team_blocks
    left join unnest(json_query_array(json_query(team_blocks.team_block, '$.squad_payload'), '$')) as squad_el
    left join unnest(json_query_array(json_query(squad_el, '$.players'), '$')) as player_el
)

select
    league_code,
    raw_ingested_at,
    team_id,
    safe_cast(json_value(player_el, '$.id') as int64) as player_id,
    {{ decode_html_entities("json_value(player_el, '$.name')") }} as player_name,
    safe_cast(json_value(player_el, '$.age') as int64) as age,
    safe_cast(json_value(player_el, '$.number') as int64) as shirt_number,
    json_value(player_el, '$.position') as position,
    json_value(player_el, '$.photo') as player_photo_url
from player_rows
