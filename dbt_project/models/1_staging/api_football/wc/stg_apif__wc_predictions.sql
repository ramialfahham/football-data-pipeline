with src as (
    select *
    from {{ source('api_football', 'raw_apif_wc_predictions') }}
),

blocks as (
    select
        'WC' as league_code,
        src.ingested_at as raw_ingested_at,
        block
    from src,
        unnest(json_query_array(json_query(src.payload, '$.response'), '$')) as block
),

pred_lines as (
    select
        league_code,
        raw_ingested_at,
        pred,
        safe_cast(json_value(block, '$.fixture_id') as int64) as fixture_id
    from blocks,
        unnest(
            json_query_array(json_query(block, '$.predictions'), '$')
        ) as pred
)

select
    league_code,
    raw_ingested_at,
    fixture_id,
    pred as prediction_doc,
    to_json_string(pred) as prediction_json
from pred_lines
