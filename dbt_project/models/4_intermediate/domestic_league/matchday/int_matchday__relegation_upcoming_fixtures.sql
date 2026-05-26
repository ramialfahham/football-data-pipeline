{{ config(materialized='table') }}

{#
  BL1 relegation play-off fixtures (API labels: Final; historic rounds list may include Relegation Round).
  Subset of int_matchday__upcoming_round_fixtures — same grain and columns.
#}

select *
from {{ ref('int_matchday__upcoming_round_fixtures') }}
where
    league_code = 'BL1'
    and round_name in {{ bl1_relegation_round_names_in_clause() }}
