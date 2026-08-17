{{ config(severity = 'error') }}

-- EVENT-LOSS DETECTOR (GitLab #75). Fails when `fct_fixture_event` holds an event that
-- `base_apif__fixture_events` no longer has.
--
-- WHY THIS CLASS WAS INVISIBLE. The fact is INCREMENTAL and accumulates; base is a TABLE rebuilt
-- from whatever raw currently holds. So when a fixture's raw payload loses events, the fact keeps
-- them and base quietly drops them, and the two disagree with nothing to say so. Every existing
-- test passed while 29 real events — including a full penalty shootout — were destroyed. It
-- surfaced days later only as an unrelated `fct_fixture_event.player_sk -> dim_player` orphan,
-- which is why it first looked like a player problem rather than data loss.
--
-- DIRECTION MATTERS, and only one direction is a defect:
--   fact > base  -> LOSS. Raw no longer carries an event the warehouse already recorded. FAIL.
--   fact < base  -> LAG. The incremental model has not picked the fixture up yet. Not a defect,
--                   and deliberately not flagged, or every fresh ingest would go red. The query is
--                   driven FROM the fact, so that direction cannot fail here.
--
-- ⚠ SCOPE IS TAKEN FROM THE FIXTURE, NOT FROM BASE — do not "simplify" it back. An earlier draft
-- scoped by `max(raw_ingested_at)` grouped over `base_apif__fixture_events` itself. That has a
-- blind spot exactly where it matters most: if a fixture loses ALL of its events, base holds zero
-- rows for it, the grouped CTE produces no row, and an inner join silently drops every one of that
-- fixture's events from the result — the TOTAL-loss case, undetectable at any cutoff, forever.
-- The known #75 incident was partial for all 5 fixtures, so measuring against it could not reveal
-- the gap; analytics-engineer-reviewer found it by reading the join. Scoping on `fct_fixture`
-- (one row per fixture, always present) removes the dependency on base having survivors.
--
-- ⚠ SCOPED BY KICKOFF DATE, and the reason is not tidiness. The known backlog (5 fixtures, 29
-- events, kickoffs 2026-08-08 and 2026-08-15) is UNREPAIRABLE — verified live against the
-- provider, which no longer returns those events — so asserting over it would block every build on
-- damage nobody can fix. The cutoff excludes it permanently and unambiguously, because a kickoff
-- date never moves (unlike an ingest timestamp, which those fixtures kept refreshing while their
-- 3-day retry window stayed open).
-- ⚠ Consequence stated rather than hidden: this is INERT for fixtures before the cutoff. Its logic
-- is PROVEN — 0 rows at the shipped cutoff and exactly the 29 known rows at 2026-08-01, both RUN
-- against prod — but a green run over a window with no fixtures in it is not evidence.
-- ⚠ Do NOT raise the cutoff to silence a future failure. A new failure means new loss, which is
-- the thing this exists to catch. Lower it once the backlog is resolved, and record why.

with in_scope as (
    select fixture_sk
    from {{ ref('fct_fixture') }}
    where fixture_date >= date('{{ var("event_loss_detector_from") }}')
)

select
    fact.fixture_sk,
    fact.event_index,
    fact.league_code,
    fact.event_type,
    fact.player_name_snapshot
from {{ ref('fct_fixture_event') }} as fact
inner join in_scope
    on fact.fixture_sk = in_scope.fixture_sk
left join {{ ref('base_apif__fixture_events') }} as still_present
    on
        fact.fixture_sk = still_present.fixture_id
        and fact.event_index = still_present.event_index
where still_present.fixture_id is null
