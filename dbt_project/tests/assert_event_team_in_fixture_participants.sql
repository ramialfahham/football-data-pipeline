{{ config(severity = 'error', store_failures = true) }}

-- Integrity guard (#526): every non-null event team_sk must be one of its fixture's two
-- participants. A violation means an event is attributed to a team that did not play the
-- fixture — a provider mis-attribution or duplicate team id. Known cases are corrected upstream
-- by seeds/fixture_team_id_overrides.csv; this test fails (ERROR) on any new occurrence, so the
-- standing DQ scan catches the class as coverage expands (#546). Scoped to fixtures whose two
-- participants are both known — NULL-safe: a fixture missing a participant id is a separate defect,
-- not flagged here, and the explicit IS NOT NULL guards avoid the NOT IN (NULL, ...) -> UNKNOWN trap.
select
    e.fixture_sk,
    e.event_index,
    e.team_sk,
    e.league_code
from {{ ref('fct_fixture_event') }} as e
inner join {{ ref('fct_fixture') }} as f
    on e.fixture_sk = f.fixture_sk
where
    e.team_sk is not null
    and f.home_team_sk is not null
    and f.away_team_sk is not null
    and e.team_sk not in (f.home_team_sk, f.away_team_sk)
