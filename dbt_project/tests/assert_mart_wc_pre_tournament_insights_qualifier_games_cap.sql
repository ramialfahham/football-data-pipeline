{{
    config(
        tags=["dq", "mart", "wc", "pretournament"]
    )
}}

-- One qualifying campaign per confederation (seed qualifier_season_api_year).
-- CONMEBOL round-robin ceiling ~18; allow headroom for intercontinental playoffs.
select
    team_sk,
    qualifier_games_played
from {{ ref('mart_wc_pre_tournament_insights') }}
where qualifier_games_played > 20
