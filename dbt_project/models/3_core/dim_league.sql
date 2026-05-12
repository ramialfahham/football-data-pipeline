{{ config(materialized='table') }}

with import_base_apif__league_entity as (
    select * from {{ ref('base_apif__league_entity') }}
)

select
    cast(league_api_id as int64) as league_sk,
    league_code,
    league_api_id,
    league_name,
    league_type,
    league_country,
    league_logo_url,
    country_flag_url,
    raw_ingested_at
from import_base_apif__league_entity
