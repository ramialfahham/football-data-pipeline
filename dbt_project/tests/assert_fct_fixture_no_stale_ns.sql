{{ config(tags=['freshness_check'], store_failures = true) }}

-- Fail if any fixture still shows NS long after scheduled kickoff, beyond the ingest SLA.
--
-- Uses a longer wall-clock window than live API freshness: this project typically runs
-- once-daily ingest (see docs/match_preview_pages_refinement.md / operations guide).
-- A 3h threshold fails CI whenever the warehouse has not refreshed since kickoff—even
-- when the pipeline is behaving on its daily cadence. ~30h allows one schedule cycle
-- plus slack; persistent NS past that indicates a missed ingest or stuck raw payload.
--
-- Tagged freshness_check: excluded from PR CI (no ingestion runs there).
-- Runs in dbt-scheduled.yml via the dq selector, after ingestion.
select fixture_sk
from {{ ref('fct_fixture') }}
where
    status_short = 'NS'
    and kickoff_datetime < timestamp_sub(current_timestamp(), interval 30 hour)
