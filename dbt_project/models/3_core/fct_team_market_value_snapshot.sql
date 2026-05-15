{{ config(materialized='table') }}

{#
  Team-level squad market value estimates (published-style total in EUR).
  Grain: (team_sk, as_of_date, source_code). Loaded from seed wc_team_market_value_snapshot
  (twice-monthly updates; future: external ingest into raw then staging).
#}

select
    cast(team_sk as int64) as team_sk,
    cast(as_of_date as date) as as_of_date,
    safe_cast(market_value_eur as int64) as market_value_eur,
    cast(source_code as string) as source_code,
    cast(prompt_version as string) as prompt_version
from {{ ref('wc_team_market_value_snapshot') }}
where team_sk is not null
