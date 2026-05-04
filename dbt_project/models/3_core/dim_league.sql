{{ config(materialized='table') }}

with bl1_leagues as (
    select * from {{ ref('base_apif__bl1_leagues') }}
),

wc26_leagues as (
    select * from {{ ref('base_apif__wc26_leagues') }}
),

all_leagues as (
    {{ union_all(['bl1_leagues', 'wc26_leagues']) }}
),

latest_per_league as (
    select
        *,
        row_number() over (
            partition by league_api_id
            order by season_api_year desc, raw_ingested_at desc
        ) as rn
    from all_leagues
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
from latest_per_league
where rn = 1
