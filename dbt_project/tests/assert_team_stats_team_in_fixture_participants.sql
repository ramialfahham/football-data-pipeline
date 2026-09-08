{{ config(severity = 'error') }}

-- Integrity guard: every non-null team-stat team_sk must be one of its fixture's two participants.
-- A violation means a match statistics line is attributed to a team that did not play the fixture —
-- a provider mis-attribution or duplicate team id. Known cases are corrected upstream by
-- seeds/fixture_team_id_overrides.csv; this test fails (ERROR) on any new occurrence.
--
-- Sibling of assert_event_team_in_fixture_participants, which has guarded the EVENTS feed since
-- #526. This one did not exist, and the gap kept a defect alive that had already been diagnosed:
-- the Macau/Mação mis-attribution was registered in the seed under #53, the override was applied to
-- events only, and the same fixture's statistics line stayed wrong in prod for months because no
-- test looked at this feed.
--
-- Scoped to fixtures whose two participants are both known — NULL-safe: a fixture missing a
-- participant id is a separate defect, not flagged here, and the explicit IS NOT NULL guards avoid
-- the NOT IN (NULL, ...) -> UNKNOWN trap.
select
    s.fixture_sk,
    s.team_sk,
    s.league_code
from {{ ref('fct_fixture_team_stats') }} as s
inner join {{ ref('fct_fixture') }} as f
    on s.fixture_sk = f.fixture_sk
where
    s.team_sk is not null
    and f.home_team_sk is not null
    and f.away_team_sk is not null
    and s.team_sk not in (f.home_team_sk, f.away_team_sk)
