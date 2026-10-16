-- Every meeting in mart_head_to_head's recent_meetings names a fixture of fct_fixture. Returns a
-- row (= fails) per meeting whose fixture_api_id is missing or names no fixture.
{{ config(store_failures = true) }}

select
    h.team_sk,
    h.opponent_team_sk,
    m.fixture_api_id,
    m.kickoff_datetime
from {{ ref('mart_head_to_head') }} as h
cross join unnest(h.recent_meetings) as m
left join {{ ref('fct_fixture') }} as f
    on m.fixture_api_id = f.fixture_sk
where f.fixture_sk is null
