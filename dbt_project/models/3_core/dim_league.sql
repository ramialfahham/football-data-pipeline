{{ config(materialized='table') }}

with src as (
    select
        league_code,
        league_api_id,
        league_name,
        league_type,
        country as league_country,
        league_logo_url,
        country_flag_url,
        raw_ingested_at
    from {{ ref('stg_apif__d1_leagues') }}
    where league_api_id is not null
),

ranked as (
    select
        *,
        row_number() over (
            partition by league_code, league_api_id
            order by raw_ingested_at desc
        ) as rn
    from src
)

select
    {{ dbt_utils.generate_surrogate_key(['league_code', 'league_api_id']) }} as league_sk,
    league_code,
    league_api_id,
    league_name,
    league_type,
    league_country,
    league_logo_url,
    country_flag_url,
    raw_ingested_at
from ranked
where rn = 1
