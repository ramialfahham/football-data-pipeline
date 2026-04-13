with src as (
    select *
    from {{ source('api_football', 'raw_d1_apif_predictions') }}
),

blocks as (
    select
        coalesce(json_value(src.payload, '$.league_code'), 'D1') as league_code,
        src.ingested_datetime as raw_ingested_datetime,
        block
    from src,
    unnest(json_query_array(json_query(src.payload, '$.response'), '$')) as block
),

pred_lines as (
    select
        league_code,
        raw_ingested_datetime,
        safe_cast(json_value(block, '$.fixture_id') as int64) as fixture_id,
        pred
    from blocks,
    unnest(
        json_query_array(json_query(block, '$.predictions'), '$')
    ) as pred
)

select
    league_code,
    raw_ingested_datetime,
    fixture_id,
    pred as prediction_doc,
    to_json_string(pred) as prediction_json
from pred_lines
