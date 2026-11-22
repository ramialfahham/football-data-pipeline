{{ config(severity = 'error', store_failures = true) }}

-- A match statistics line filed under a team that did not play the match (a provider mis-attribution
-- or a duplicate team id) is flagged team_needs_research in base and is on
-- mart_competition_research_list; fct_fixture_team_stats builds its rows from the match's own two
-- teams, so the line reaches no fact. Known cases are corrected upstream by
-- seeds/fixture_team_id_overrides.csv. Returns a line filed under a non-participant that is not
-- flagged, which means the flag failed. Scoped to matches whose two participants are known: a match
-- missing a participant id is a separate defect. It reads the base statistics, not the fact: the
-- fact builds its team rows from the fixture's own participants, so a check against it could never
-- fail.
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
    and not s.team_needs_research
