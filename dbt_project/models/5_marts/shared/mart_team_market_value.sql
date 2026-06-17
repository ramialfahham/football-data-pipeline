{{ config(materialized='view') }}

{#
  WC national teams: latest published-style squad market value estimate (EUR).
  Grain: one row per team_sk. Canonical metric name: market_value_eur.

  The WC team set comes from dim_team_competition_season_mapping (the conformed
  team↔competition↔season membership), NOT dim_team.league_code — that latest-ingest
  provenance stamp was dropped when dim_team became a pure entity (Phase 2), and it
  surfaced only an incomplete WC set anyway. dim_team supplies identity attributes only.
#}

with latest as (
    select * from {{ ref('int_team__market_value_latest') }}
),

wc_teams as (
    select distinct team_sk
    from {{ ref('dim_team_competition_season_mapping') }}
    where league_code = 'WC'
),

dim_team as (
    select
        team_sk,
        team_api_id,
        team_name,
        team_country
    from {{ ref('dim_team') }}
)

select
    w.team_sk,
    d.team_api_id,
    'WC' as league_code,
    d.team_name,
    d.team_country,
    l.as_of_date,
    l.market_value_eur,
    l.source_code,
    l.prompt_version
from wc_teams as w
inner join dim_team as d
    on w.team_sk = d.team_sk
left join latest as l
    on w.team_sk = l.team_sk
