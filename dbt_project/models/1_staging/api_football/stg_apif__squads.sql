with src as (
    select *
    from {{ source('api_football', 'raw_apif_squads') }}
    -- Complete snapshot per run (/players/squads re-fetched every run per team), so select the
    -- latest ingestion snapshot per league_code before flattening — same as stg_apif__players.
    qualify row_number() over (partition by league_code order by ingested_at desc) = 1
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

player_rows as (
    select
        league_code,
        raw_ingested_at,
        team_id,
        player_el
    from team_blocks,
        unnest(json_query_array(json_query(team_block, '$.squad_payload'), '$')) as squad_el,
        unnest(json_query_array(json_query(squad_el, '$.players'), '$')) as player_el
)

select
    league_code,
    raw_ingested_at,
    team_id,
    safe_cast(json_value(player_el, '$.id') as int64) as player_id,
    json_value(player_el, '$.name') as player_name,
    safe_cast(json_value(player_el, '$.age') as int64) as age,
    safe_cast(json_value(player_el, '$.number') as int64) as shirt_number,
    json_value(player_el, '$.position') as position,
    json_value(player_el, '$.photo') as player_photo_url
from player_rows
