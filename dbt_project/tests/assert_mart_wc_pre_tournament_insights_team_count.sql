{{
    config(
        tags=["dq", "mart", "wc", "pretournament"]
    )
}}

-- Registry team_count for WC is 48; participant list must match current tournament season on fct_fixture.

select count(*) as team_count
from {{ ref('mart_wc_pre_tournament_insights') }}
having count(*) != 48
