{{
    config(
        tags=["dq", "mart", "season_profile"]
    )
}}

-- BL1: advanced profile game count must match mart_team_season.played when both are present.

select
    team_season_sk,
    team_sk,
    season_games_played,
    played
from {{ ref('mart_team_season_profile') }}
where
    league_code = 'BL1'
    and played is not null
    and season_games_played != played
