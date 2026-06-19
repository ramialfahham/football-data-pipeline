# Review — fix/idle-snapshot-completeness — 2026-06-19

> PR1 of 2: enforce the append-complete-snapshot invariant at the fixtures write boundary (carry forward
> the prior snapshot's seasons in poll/idle mode) so the full-refresh fct_fixture stops losing history.
> No dbt change. Round 2: the data-engineer round-1 FAIL (sample-payload rule + quota-exhaustion stale
> write) is resolved — a real committed `/fixtures` sample under tests/fixtures/apif/ + an empty-fetch
> early-return. Required reviewers for the staged paths: scope-auditor (always), data-engineer-reviewer
> (ingestion + data_contract), cto-reviewer (tests). diff_sha256 covers code + contract.md.

diff_sha256: 00bcaf5fe479e2e6bb1d2a0d9a0970e7f778dbfd49836ded5e40099ad4f23175

## scope-auditor
VERDICT: PASS
risks_checked:
- Carry-forward under the thin-cache recovery path: a pre-recovery thin latest snapshot carries nothing forward (no recursive truncation); the contract documents the interim state and the post-merge recovery that re-establishes completeness; `test_thin_cache_carries_nothing` confirms it. All five diff files are within scope_paths (incl. `tests/fixtures/apif/**` added via the recorded amendment).
- Amendment validity + no silent §10: the `amendments:` entry quotes the authority (data-engineer Finding 1 + CPO option-(a) ruling) and adds the minimal scope (one fixtures dir, one real sample file — pure test data, not a product/metric decision); deferred items untouched (no dbt materialization change, no PR2 FK-test restoration, no recovery run, no backfill); Appendix-A clean (the fix un-masks rather than introduces a masked test). data_contract.md edit is a doc-accuracy match to the code, and it rides in the diff (doc-sync satisfied).

## data-engineer-reviewer
VERDICT: PASS
risks_checked:
- Round-1 Finding 1 (sample-payload rule, CPO 2026-06-12) RESOLVED: `tests/fixtures/apif/bl1_fixtures_next_merged.json` exists and is a real-shaped provider payload (real fixture ids 871164/1048881/1223975, real team ids, real FT status from BL1 RAW); the carry-forward / team-scoping / full-mode tests load and slice it via `_sample_response()`. Rule satisfied.
- Round-1 Finding 2 (quota-exhaustion stale write) RESOLVED: on `n_fx == 0` the function returns early `(fixtures_merged, set(), set())` before the carry-forward and before `load_json_to_bq`, preserving the prior snapshot; error still logged; `test_empty_fresh_fetch_does_not_write` + `test_quota_exhausted_before_fetch_does_not_write` confirm no write.
- Carry-forward correctness (no current-season duplication): `fetched_seasons` is derived from `fixtures_merged` after the loop (which already merged cache-reused complete seasons), so the `not in fetched_seasons` filter can never re-add a season already present; full mode is a no-op; `from_to`/`next` modes are doubly gated by `skip_eligible`. No WRITE_TRUNCATE (append=True kept), raw schema/naming unchanged, no cost/scope knob change (carry-forward is an in-memory merge, zero extra API calls).

## cto-reviewer
VERDICT: PASS
risks_checked:
- Genuine regression guards: `test_poll_single_season_carries_forward_history` and `test_team_ids_scoped_to_fetched_season` FAIL against pre-fix code (written seasons would be `{2024}` not `{2022,2023,2024}`); both `TestEmptyFreshFetchWritesNothing` tests FAIL if the `n_fx == 0` early-return is removed (the write would fire). Not vacuous.
- Mock hermetic integrity + fixture robustness: BigQuery + HTTP fully mocked; the quota test patches `ingestion.api_football.quota._http_quota_exhausted` (same module object the loader reads) and restores on exit, no leakage; the sample is loaded via `Path(__file__).parent/...` (CWD-independent), valid JSON, and its team/fixture ids match the test constants exactly. `python -m pytest tests/` discovers the file (same convention as the sibling cache-skip test).

## escalations
(none)
