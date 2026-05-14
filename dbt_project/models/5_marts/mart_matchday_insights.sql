{{ config(materialized='view') }}

{#
  Stable relation name for scripts and GitHub Pages export (marts.mart_matchday_insights).
  Thin view over BL1 only: the static match-preview UI is not multi-competition yet.
  WC lives in mart_matchday_insights_wc (same column contract); union for export when UI is ready.
#}

select * from {{ ref('mart_matchday_insights_bl1') }}
