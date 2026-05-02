-- Fail if any fixture that kicked off more than 3 hours ago is still NS (Not Started).
-- A match cannot still be "not started" hours after its scheduled kickoff.
-- This catches ingestion staleness: if the daily ingest missed a matchday, finished
-- games remain NS and form window metrics silently use older rounds instead.
select fixture_sk
from {{ ref('fct_fixture') }}
where
    status_short = 'NS'
    and kickoff_datetime < timestamp_sub(current_timestamp(), interval 3 hour)
