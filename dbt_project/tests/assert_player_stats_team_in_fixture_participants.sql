{{ config(severity = 'error') }}

-- Integrity guard: every non-null player-stat team_sk must be one of its fixture's two
-- participants. A violation means a lineup is attributed to a team that did not play the fixture —
-- a provider mis-attribution or duplicate team id. Known cases are corrected upstream by
-- seeds/fixture_team_id_overrides.csv; this test fails (ERROR) on any new occurrence.
--
-- Sibling of assert_event_team_in_fixture_participants, which has guarded the EVENTS feed since
-- #526. This one did not exist, and the gap is what let API-Football file a BSA lineup under a
-- team id it had sent with a null name: nothing objected until the unnameable id reached dim_team
-- days later, where not_null on team_name stopped the whole nightly build with no indication of
-- which fixture had caused it.
--
-- Scoped to fixtures whose two participants are both known — NULL-safe: a fixture missing a
-- participant id is a separate defect, not flagged here, and the explicit IS NOT NULL guards avoid
-- the NOT IN (NULL, ...) -> UNKNOWN trap.
select
    p.fixture_sk,
    p.player_sk,
    p.team_sk,
    p.league_code
from {{ ref('fct_fixture_player_stats') }} as p
inner join {{ ref('fct_fixture') }} as f
    on p.fixture_sk = f.fixture_sk
where
    p.team_sk is not null
    and f.home_team_sk is not null
    and f.away_team_sk is not null
    and p.team_sk not in (f.home_team_sk, f.away_team_sk)
