{{ config(materialized='view') }}

{#
  Stable relation name for scripts and GitHub Pages export (marts.mart_matchday_insights).
  Logic and tests live on mart_matchday_insights_bl1; add mart_matchday_insights_wc later
  as a sibling mart with the same column contract.
#}

select * from {{ ref('mart_matchday_insights_bl1') }}
