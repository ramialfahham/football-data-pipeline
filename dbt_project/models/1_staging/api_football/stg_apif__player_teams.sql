with src as (
    -- INCREMENTAL accumulation: the /players/teams loader is skip-if-present, so each ingestion
    -- snapshot holds only that run's NEW players. UNION ALL snapshots (no latest-snapshot select).
    -- Faithful 1:1 flatten only; no entity dedup here — base assembles current-per-player. See
    -- the incremental-accumulation note in stg_apif__generic.yml.
    select *
    from {{ source('api_football', 'raw_apif_player_teams') }}
),

player_blocks as (
    select
        src.ingested_at as raw_ingested_at,
        src.league_code,
        player_block,
        safe_cast(json_value(player_block, '$.player_id') as int64) as player_id
    from src,
        unnest(json_query_array(json_query(src.payload, '$.response'), '$')) as player_block
),

team_blocks as (
    select
        league_code,
        raw_ingested_at,
        player_id,
        team_el
    from player_blocks,
        unnest(json_query_array(json_query(player_block, '$.teams_payload'), '$')) as team_el
)

select
    league_code,
    raw_ingested_at,
    player_id,
    safe_cast(json_value(team_el, '$.team.id') as int64) as team_id,
    json_value(team_el, '$.team.name') as team_name,
    safe_cast(season_str as int64) as season_year
from team_blocks,
    unnest(json_value_array(json_query(team_el, '$.seasons'))) as season_str
