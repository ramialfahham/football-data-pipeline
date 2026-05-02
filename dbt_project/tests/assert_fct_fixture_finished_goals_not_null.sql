-- Fail if any finished fixture has null goals_home or goals_away.
-- A finished match must always have both goal values; nulls indicate a failed or incomplete ingestion.
select fixture_sk
from {{ ref('fct_fixture') }}
where
    status_short in ('FT', 'AET', 'PEN')
    and (goals_home is null or goals_away is null)
