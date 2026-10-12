# Review — feat/provider-refetch

diff_sha256: 1dc7623dbb1502f5797eac7a02e83fb601eabd4f081f7f4bd65d2bf0397b5459

rounds: 5

rounds_cap_override: rounds four and five cover only the lint fixes the pre-commit hook demanded after round 3; approved in chat, 2026-10-12.

## scope-auditor
VERDICT: PASS
risks_checked:
- The cumulative diff touches only scripts/refetch_from_provider.py, tests/test_refetch_from_provider.py and .claude/task/contract.md, all in scope_paths; no unrecorded amendment.
- Every decision in the code is one the contract records as approved: the refetch, its two lists, the not-worse guard, the call cap, the ingest lock, the 02:00 to 04:00 UTC refusal and the 250 ms pacing. The 60-minute lease, the 50-minute call window, the per-team comparison and the refusal while raw holds rows staging has not read only narrow the approved behaviour.
- Reserved items stay undecided: plan mode is the default and makes no call, a run needs --max-calls and is started by hand, and no model, seed or schedule is touched.
- Section 10 thresholds: no new mechanism, dependency, workflow or recurring cost; Appendix A: nothing found.

## platform-reviewer
VERDICT: PASS
risks_checked:
- The lock: credentials and client are read before it is taken, the try/finally starts right after it, and the lease (60 minutes from a start before 02:00) ends before the 04:00 nightly; tests pin the order, the lease size and the release on failure.
- The call cap and the 50-minute call window: CallCounter counts retries, makes no call past either and latches the daily-limit flag, so the loaders write nothing unfinished; tested in isolation, through fetch_json and through main.
- The not-worse guard: its counts match what stg_apif__fixture_events, stg_apif__fixture_players and stg_apif__fixture_statistics count, per team; a fixtures run is refused while raw holds a newer row than the staging build; the stored-counts parsing and the staging-age check are tested, and both queries dry-run valid on BigQuery.
- Squads mode fetches exactly the listed team-seasons through load_squad_players_batch; tested on its arguments.
- Round 4: the 250 ms pacing default now set in main() on the run path, before any call (an operator's own value still wins), the import wrap, the instance attribute on _CapReached and the test stub change nothing else; tested.
- Round 5: the google.cloud import above the sys.path block and the noqa E402 markers on the repo imports, as in scripts/check_registry_var_sync.py, change only the lint result; every pre-commit hook passes.

## escalations
(none)
