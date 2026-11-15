-- Fail if any finished fixture has null goals_home or goals_away.
-- A finished match must always have both goal values; nulls indicate a failed or incomplete ingestion.
-- A withheld result (result_needs_research) is blank by design and is checked by its own test.
{{ config(store_failures = true) }}

select fixture_sk
from {{ ref('fct_fixture') }}
where
    status_short in ('FT', 'AET', 'PEN')
    and not result_needs_research
    and (goals_home is null or goals_away is null)
