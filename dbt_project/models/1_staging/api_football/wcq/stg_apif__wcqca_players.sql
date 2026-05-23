with src as (
    select *
    from {{ source('api_football', 'raw_apif_wcqca_players') }}
),

team_blocks as (
    select
        'WCQCA' as league_code,
        src.ingested_at as raw_ingested_at,
        team_block
    from src,
        unnest(json_query_array(json_query(src.payload, '$.response'), '$')) as team_block
),

player_rows as (
    select
        league_code,
        raw_ingested_at,
        player_el,
        safe_cast(json_value(team_block, '$.team_id') as int64) as team_id,
        safe_cast(json_value(team_block, '$.season') as int64) as season_year
    from team_blocks,
        unnest(
            json_query_array(json_query(team_block, '$.players_payload'), '$')
        ) as player_el
)

select
    league_code,
    raw_ingested_at,
    team_id,
    season_year,
    safe_cast(json_value(player_el, '$.player.id') as int64) as player_id,
    json_value(player_el, '$.player.name') as player_name,
    json_value(player_el, '$.player.firstname') as player_firstname,
    json_value(player_el, '$.player.lastname') as player_lastname,
    json_value(player_el, '$.player.photo') as player_photo_url,
    safe_cast(json_value(player_el, '$.player.birth.date') as date) as birth_date,
    json_value(player_el, '$.player.nationality') as nationality,
    json_query(player_el, '$.statistics') as statistics_json,
    to_json_string(player_el) as source_json
from player_rows
