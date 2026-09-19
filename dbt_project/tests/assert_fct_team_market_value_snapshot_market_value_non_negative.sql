{{
    config(
        tags=["dq", "core", "market_value"],
        store_failures = true
    )
}}

-- Fail when market_value_eur is negative. Null is allowed (no estimate loaded yet).

select
    team_sk,
    as_of_date,
    source_code,
    market_value_eur
from {{ ref('fct_team_market_value_snapshot') }}
where market_value_eur < 0
