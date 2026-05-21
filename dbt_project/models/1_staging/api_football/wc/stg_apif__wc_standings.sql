with src as (
    select *
    from {{ source('api_football', 'raw_apif_wc_standings') }}
),

expanded_standings as (
    select
        'WC' as league_code,
        src.ingested_at as raw_ingested_at,
        league_block,
        stage_group,
        team_row,
        to_json_string(json_query(src.payload, '$.errors')) as api_errors_json,
        safe_cast(json_value(src.payload, '$.results') as int64) as api_reported_result_count,
        to_json_string(json_query(src.payload, '$.parameters')) as request_parameters_json
    from src,
        unnest(json_query_array(json_query(src.payload, '$.response'), '$')) as league_block,
        unnest(json_query_array(json_query(league_block, '$.league.standings'), '$')) as stage_group,
        unnest(json_query_array(stage_group, '$')) as team_row
)

select
    league_code,
    raw_ingested_at,
    api_errors_json,
    api_reported_result_count,
    request_parameters_json,
    safe_cast(json_value(league_block, '$.league.id') as int64) as league_api_id,
    json_value(league_block, '$.league.name') as league_name,
    safe_cast(json_value(league_block, '$.league.season') as int64) as season,
    safe_cast(json_value(team_row, '$.rank') as int64) as standing_rank,
    safe_cast(json_value(team_row, '$.team.id') as int64) as team_id,
    json_value(team_row, '$.team.name') as team_name,
    safe_cast(json_value(team_row, '$.points') as int64) as points,
    safe_cast(json_value(team_row, '$.goalsDiff') as int64) as goals_diff,
    json_value(team_row, '$.form') as form,
    -- For tournaments with groups (WC, WCQ*) the group letter lives at
    -- $.group (e.g. 'Group A'). $.description is the qualification status
    -- ('8th Finals' etc.), unrelated to the group. Domestic leagues still
    -- read $.description elsewhere for relegation/promotion zone labels.
    json_value(team_row, '$.group') as group_description,
    safe_cast(json_value(team_row, '$.all.played') as int64) as played_all,
    safe_cast(json_value(team_row, '$.all.win') as int64) as wins_all,
    safe_cast(json_value(team_row, '$.all.draw') as int64) as draws_all,
    safe_cast(json_value(team_row, '$.all.lose') as int64) as losses_all,
    to_json_string(team_row) as source_json
from expanded_standings
