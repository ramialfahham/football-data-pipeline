{{ config(materialized='view') }}

{#
  Latest market_value_eur snapshot per team (max as_of_date, then source_code for tie-break).
#}

with ranked as (
    select
        team_sk,
        as_of_date,
        market_value_eur,
        source_code,
        prompt_version,
        row_number() over (
            partition by team_sk
            order by as_of_date desc, source_code desc
        ) as snapshot_rank
    from {{ ref('fct_team_market_value_snapshot') }}
)

select
    team_sk,
    as_of_date,
    market_value_eur,
    source_code,
    prompt_version
from ranked
where snapshot_rank = 1
