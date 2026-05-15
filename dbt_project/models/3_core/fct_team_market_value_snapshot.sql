{{ config(materialized='table') }}

{#
  Team-level squad market value estimates (published-style total in EUR).
  Grain: (team_sk, as_of_date, source_code). Loaded from seed wc_team_market_value_snapshot
  (twice-monthly updates; future: external ingest into raw then staging).
#}

with import_wc_team_market_value_snapshot as (
    select * from {{ ref('wc_team_market_value_snapshot') }}
),

seed_rows as (
    select
        cast(team_sk as int64) as team_sk,
        as_of_date as as_of_date_raw,
        cast(source_code as string) as source_code,
        cast(prompt_version as string) as prompt_version,
        safe_cast(market_value_eur as int64) as market_value_eur
    from import_wc_team_market_value_snapshot
    where team_sk is not null
),

final as (
    select
        team_sk,
        source_code,
        prompt_version,
        market_value_eur,
        coalesce(
            safe_cast(as_of_date_raw as date),
            safe.parse_date('%Y-%m-%d', cast(as_of_date_raw as string)),
            safe.parse_date('%Y%m%d', cast(as_of_date_raw as string))
        ) as as_of_date
    from seed_rows
)

select
    team_sk,
    as_of_date,
    source_code,
    prompt_version,
    market_value_eur
from final
