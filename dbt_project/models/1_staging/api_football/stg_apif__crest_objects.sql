with src as (
    select *
    from {{ source('api_football', 'raw_apif_crest_objects') }}
    qualify row_number() over (order by ingested_at desc) = 1
)

select
    src.ingested_at as raw_ingested_at,
    json_value(crest_object, '$.kind') as crest_kind,
    safe_cast(json_value(crest_object, '$.id') as int64) as provider_id,
    json_value(crest_object, '$.status') as crest_status,
    json_value(crest_object, '$.sha256') as source_sha256,
    safe_cast(json_value(crest_object, '$.fetched_at') as timestamp) as fetched_at,
    safe_cast(json_value(crest_object, '$.checked_at') as timestamp) as checked_at
from src,
    unnest(json_query_array(src.payload, '$.objects')) as crest_object
