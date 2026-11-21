{{ config(severity = 'error', store_failures = true) }}

-- Integrity guard: every non-null team-stat team id in base must be one of its fixture's two participants.
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
-- It reads the base statistics, not the fact: the fact builds its team rows from the fixture's own
-- participants, so a check against it could never fail.
select
    f.fixture_sk,
    s.team_id as team_api_id,
    s.league_code
from {{ ref('base_apif__fixture_statistics') }} as s
inner join {{ ref('fct_fixture') }} as f
    on s.fixture_id = f.fixture_api_id
where
    s.team_id is not null
    and f.home_team_api_id is not null
    and f.away_team_api_id is not null
    and s.team_id not in (f.home_team_api_id, f.away_team_api_id)
