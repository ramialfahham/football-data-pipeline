-- Fail if any finished fixture has goals outside the plausible range [0, 20].
-- Catches swapped or corrupted goal values from the API.
select fixture_sk
from {{ ref('fct_fixture') }}
where
    status_short in ('FT', 'AET', 'PEN')
    and goals_home is not null
    and goals_away is not null
    and (
        goals_home < 0 or goals_home > 20
        or goals_away < 0 or goals_away > 20
    )
