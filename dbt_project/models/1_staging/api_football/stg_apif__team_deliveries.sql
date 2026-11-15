with src as (
    select
        league_code,
        ingested_at,
        payload
    from {{ source('api_football', 'raw_apif_teams') }}
)

select
    src.league_code,
    src.ingested_at as raw_ingested_at,
    safe_cast(json_value(row_json, '$.team.id') as int64) as team_id,
    {{ decode_html_entities("json_value(row_json, '$.team.country')") }} as team_country
from src,
    unnest({{ apif_payload_response_json_strings('src') }}) as row_json
