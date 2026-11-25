-- Home's boards are read at the season mart_home_rotation names. Where the player leaderboard marks
-- a different season as the league's current one, the two definitions of "the latest season with a
-- finished match" have drifted apart, and a league would show one season under the other's label.
-- Returns one row per league on which they differ.
{{ config(severity = 'error', store_failures = true) }}

with boards_current as (
    select distinct
        league_code,
        season_api_year
    from {{ ref('mart_leaderboards') }}
    where window_type = 'season_to_date' and is_current_season
)

select
    rotation.league_code,
    rotation.season_api_year as rotation_season_api_year,
    boards_current.season_api_year as boards_season_api_year
from {{ ref('mart_home_rotation') }} as rotation
inner join boards_current
    on rotation.league_code = boards_current.league_code
where
    rotation.board_role = 'current'
    and rotation.season_api_year != boards_current.season_api_year
