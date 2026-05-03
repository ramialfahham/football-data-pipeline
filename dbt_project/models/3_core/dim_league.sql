{{ config(materialized='table') }}

with latest_per_league as (
    select
        *,
        row_number() over (
            partition by league_code, league_api_id
            order by season_api_year desc, raw_ingested_at desc
        ) as rn
    from {{ ref('base_apif__bl1_leagues') }}
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
from latest_per_league
where rn = 1
