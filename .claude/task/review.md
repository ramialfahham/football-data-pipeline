# Review — fix/player-stats-second-fetch — player stats fetched too early are fetched a second time once complete

diff_sha256: c04dc8aebd6ab56d93b26b79890528ee9172136c6878590c03d47deceac579e2

rounds: 2

## scope-auditor
VERDICT: PASS
risks_checked:
- Scope: every changed file is in scope_paths; the two amendments (docs/operations_guide.md, the idle-competition tests) carry a date and the #186 How step 3 authority; decisions_taken, decisions_reserved and the impact_map unchanged by them.
- Section 10 and thresholds: no label, metric or user-visible change; the 72-hour reading is a delegated reading; no new mechanism (existing details step and coverage read); cost declared as approved (about 143 calls once, about 2 a day, about 1.1 GB a night less BigQuery); no scheduler, cadence or run change.
- Impact map present with pasted lineage (66 models), the single writer and the measured counts; widens fetching, so not a coverage cut.
- Appendix A: no metric, product text, rule extension, consumption shortcut or frontend logic.
- Removed reader and helper have no remaining callers; data_contract.md and operations_guide.md state the new coverage meaning; no secret or escalations.log entry.

## data-engineer-reviewer
VERDICT: PASS
risks_checked:
- Append-only and idempotency: _insert_fixture_rows unchanged (WRITE_APPEND); the second fetch's ingested_at is at or after kickoff + 72 h, so a match is fetched at most once more; a failed batch stays due and retries next night.
- Completeness: a due match counts FIXTURE_PLAYERS missing until fetched; only BL1 is hard-gated; the mid-run boundary case cannot occur for BL1's kickoff times.
- Poll gate: a not-covered FIXTURE_PLAYERS falls into the conservative skip, so a due match never switches an idle competition to full mode.
- Idle wiring: run_poll_phases returns a CompetitionRunResult built as in run_cheap_phases; idle results go to Phase 2 only, per-team expectations still read active results only.
- Cost knobs: no change to history_seasons, ingest_active, cadence or caps; Phase 2 plans active competitions before idle ones.
- Raw schema and registry untouched; data_contract.md updated in the same branch.
- Round 1 note: docs/operations_guide.md's completeness sentence was stale; round 2: fixed, scope amended.

## platform-reviewer
VERDICT: PASS
risks_checked:
- Re-run and interruption safety of second_fetch_due and _needs_fetch: no re-fetch after the second fetch; an unwritten batch stays due.
- Tests: second_fetch_due boundaries (now at the delay, fetch at the delay, the 57-hour evening case, unknown times); read_coverage due and not-due cases; the _needs_fetch branch and the planner fetching only the due id with no per-league query.
- Stale callers: none of _read_fetched_coverage, batch_fixtures._fixture_details_table_id or the old poll tuple remain.
- No hook, workflow, CI, dependency, credential or site change.
- Query cost: 31 per-league queries become none; the shared read adds MAX(ingested_at) and a kickoff cast over rows it already scans.
- Round 1 FAIL: the idle-competition wiring was pinned by no test. Round 2: TestIdleCompetitionsReachTheDetailsStep (run_poll_phases returns the fixtures; an AST test that the orchestrator hands idle_results and phase1_covered to the step); each revert turns it red. Resolved.

## escalations
(none)
