{{ config(materialized='table') }}

{#
  One row per (team_sk, season_sk) for table display and marts.
  fct_standings grain can include multiple rows (e.g. group_description);
  keep the row with latest raw_ingested_at.
#}

with import_fct_standings as (
    select * from {{ ref('fct_standings') }}
)

select
    team_sk,
    season_sk,
    standing_rank,
    form,
    group_description
from import_fct_standings
qualify row_number() over (
    partition by team_sk, season_sk order by raw_ingested_at desc nulls last
) = 1
