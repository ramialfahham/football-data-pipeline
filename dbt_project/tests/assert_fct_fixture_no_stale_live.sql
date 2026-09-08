{{ config(tags=['freshness_check']) }}

-- Fail if any fixture is still ACTIVELY PLAYING more than 6 hours after its scheduled kickoff.
-- A match cannot be in its second half, in extra time or in a penalty shootout that long after it
-- started, so a fixture sitting here means the status was never updated — an ingestion failure,
-- typically the API being unreachable during the match window. That is our defect, so it is an
-- ERROR (engineering_standards.md section 3, "pipeline logic error").
--
-- ⛔ SUSP AND INT ARE DELIBERATELY NOT LISTED HERE, AND THEY ARE NOT A FRESHNESS PROBLEM AT ALL.
-- A suspended or interrupted match is VALID STATUS INFORMATION — a true fact about the world, which
-- can hold for days while a replay decision is made, and which no amount of re-ingesting changes.
-- There is nothing actionable to report about it, so it is neither an error nor a warning here.
-- Keeping it at error severity was actively harmful: ONE Eredivisie fixture sitting at INT ended the
-- 2026-09-07 nightly at PASS=405 WARN=1 ERROR=2 SKIP=672, because `dbt build` marks every dependent
-- of a failed error-severity test as skipped. That red then became routine, and an unrelated defect
-- hid behind it for three nights.
-- ⭐ What actually mattered in that incident was that a TEAM WAS A GAME SHORT of its league, not that
-- a status string was unusual — and that is reconciled against the standings' own played count by
-- assert_mart_team_season_insights_games_match_played, which catches a short record whatever caused
-- it. Status enumeration is the wrong instrument for that question; an independent authority is the
-- right one.
--
-- ⚠ THE WINDOW IS 6 HOURS, NOT 3. The condition detected here — a status that was never updated —
-- persists indefinitely, so on a once-nightly run any threshold from about 3h to 20h catches it
-- equally. What the threshold really controls is FALSE alarms on a match still legitimately in play:
-- 90 minutes plus stoppage, half time, extra time and a penalty shootout approaches 2h50 before any
-- weather or floodlight delay. At error severity a false positive costs the whole warehouse refresh.
-- The sibling assert_fct_fixture_no_stale_ns.sql made the same argument first, at 30 hours.
--
-- Tagged freshness_check: excluded from PR CI, where no ingestion runs. ⚠ That tag means this test
-- executes ONLY in the real nightly (fdp-nightly's unselected `dbt build`) — every MR job and
-- data:build:main exclude it, so a green pipeline says nothing about this file.
select fixture_sk
from {{ ref('fct_fixture') }}
where
    status_short in ('1H', 'HT', '2H', 'ET', 'BT', 'P', 'LIVE')
    and kickoff_datetime < timestamp_sub(current_timestamp(), interval 6 hour)
