with src as (
    select *
    from {{ source('api_football', 'raw_d1_apif_fixture_players') }}
),

blocks as (
    select
        coalesce(json_value(src.payload, '$.league_code'), 'D1') as league_code,
        src.ingested_datetime as raw_ingested_datetime,
        block_json
    from src,
    unnest(ifnull(json_query_array(src.payload, '$.response'), [])) as block_json
),

team_rows as (
    select
        league_code,
        raw_ingested_datetime,
        safe_cast(json_value(block_json, '$.fixture_id') as int64) as fixture_id,
        team_block
    from blocks,
    unnest(json_query_array(block_json, '$.players')) as team_block
),

players as (
    select
        league_code,
        raw_ingested_datetime,
        fixture_id,
        team_block,
        player_el
    from team_rows,
    unnest(
        json_query_array(team_block, '$.players')
    ) as player_el
)

select
    league_code,
    raw_ingested_datetime,
    fixture_id,
    safe_cast(json_value(team_block, '$.team.id') as int64) as team_id,
    json_value(team_block, '$.team.name') as team_name,
    safe_cast(json_value(player_el, '$.player.id') as int64) as player_id,
    json_value(player_el, '$.player.name') as player_name,
    json_value(player_el, '$.player.photo') as player_photo_url,
    json_query(player_el, '$.statistics') as player_statistics_json,
    to_json_string(player_el) as source_json
from players
