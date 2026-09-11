-- An awarded match must not blank a team's season statistics.
--
-- WHY THIS EXISTS. An AWD (technical loss) or WO (walkover) counts as a played
-- match for RESULTS — it has a real scoreline and the league table counts it. It has no STAT LINE
-- and never will: nobody played. The team-stat rates are gated all-or-nothing, so if that gate
-- compares coverage against `games_played` it reads the awarded match as a missing stat and NULLs
-- every statistical metric for the whole season. Measured before the fix: ~16 team-seasons, and
-- because int_team_season__deserved_vs_actual needs full shots-on-target coverage for EVERY team in
-- a league-season, the entire Ligue 1 2025 deserved-vs-actual read would have been withheld —
-- 18 teams — because of one fixture.
--
-- The gate therefore compares against `games_expecting_team_stats` (played minus awarded), and this
-- test is what pins that. Revert any of the 25 gates in int_team_season__metrics_cumulative.sql to
-- `games_played` and every team-season carrying an awarded match fails here.
--
-- ⛔ Without this test a plain reversion at any of the 35 gate sites would pass CI untouched.
--
-- Reads the whole-season projection rather than the cumulative model: same formulas, one row per
-- team-season instead of one per matchday, so a failure names a season rather than a matchday.

with season as (
    select * from {{ ref('int_team_season__metrics') }}
)

select
    team_sk,
    league_code,
    season_api_year,
    season_games_played,
    games_expecting_team_stats,
    games_with_team_stats,
    shots_per_match
from season
where
    -- the team's stat feed covers every game that COULD have one …
    games_expecting_team_stats > 0
    and games_with_team_stats >= games_expecting_team_stats
    -- … so the rate must exist. Under a gate reverted to games_played it does not, because an
    -- awarded match makes games_with_team_stats < games_played by construction.
    and shots_per_match is null
