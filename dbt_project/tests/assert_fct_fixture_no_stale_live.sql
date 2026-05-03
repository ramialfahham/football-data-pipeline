{{ config(tags=['freshness_check']) }}

-- Fail if any fixture is still in a live/in-progress status more than 3 hours
-- after its scheduled kickoff. A match cannot still be actively playing hours
-- after it should have finished. This catches ingestion failures where the
-- API was unreachable during the match window and the status was never updated.
--
-- Tagged freshness_check: excluded from PR CI (no ingestion runs there).
-- Runs in dbt-scheduled.yml via the dq selector, after ingestion.
select fixture_sk
from {{ ref('fct_fixture') }}
where
    status_short in ('1H', 'HT', '2H', 'ET', 'BT', 'P', 'SUSP', 'INT', 'LIVE')
    and kickoff_datetime < timestamp_sub(current_timestamp(), interval 3 hour)
