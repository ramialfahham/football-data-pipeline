-- #484: the player top-players strip and the team form panel must use the SAME form window.
-- Both mart_player_momentum and mart_team_momentum derive window_type from the one shared
-- selection (int_team_momentum_window), so for every upcoming fixture side present in BOTH marts
-- the window_type must be identical. A mismatch means the player path drifted off the shared
-- window (e.g. a re-introduced inline last_5) — the exact regression #484 fixed.
--
-- Inner join = "present on both sides": a side in the team mart but not the player mart is a
-- player-data coverage gap, not a window mismatch, so it is correctly ignored here.
--
-- Any returned row is a defect.

with player_sides as (
    select distinct
        upcoming_fixture_sk,
        team_sk,
        window_type
    from {{ ref('mart_player_momentum') }}
),

team_sides as (
    select
        upcoming_fixture_sk,
        team_sk,
        window_type
    from {{ ref('mart_team_momentum') }}
)

select
    p.upcoming_fixture_sk,
    p.team_sk,
    p.window_type as player_window_type,
    t.window_type as team_window_type
from player_sides as p
inner join team_sides as t
    on
        p.upcoming_fixture_sk = t.upcoming_fixture_sk
        and p.team_sk = t.team_sk
where p.window_type != t.window_type
