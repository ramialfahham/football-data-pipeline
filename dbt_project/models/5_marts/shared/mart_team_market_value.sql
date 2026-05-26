{{ config(materialized='view') }}

{#
  WC national teams: latest published-style squad market value estimate (EUR).
  Grain: one row per team_sk. Canonical metric name: market_value_eur.
#}

with latest as (
    select * from {{ ref('int_team__market_value_latest') }}
),

dim_team as (
    select * from {{ ref('dim_team') }}
    where league_code = 'WC'
)

select
    d.team_sk,
    d.team_api_id,
    d.league_code,
    d.team_name,
    d.team_country,
    l.as_of_date,
    l.market_value_eur,
    l.source_code,
    l.prompt_version
from dim_team as d
left join latest as l
    on d.team_sk = l.team_sk
