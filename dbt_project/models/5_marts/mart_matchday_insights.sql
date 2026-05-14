{{ config(materialized='view') }}

{#
  Stable relation name for scripts and GitHub Pages export (marts.mart_matchday_insights).
  Union of competition-specific marts with identical column contracts (BL1 + WC).
#}

select * from {{ ref('mart_matchday_insights_bl1') }}
union all
select * from {{ ref('mart_matchday_insights_wc') }}
