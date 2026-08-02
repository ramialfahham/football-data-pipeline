# Review — fix/890-prune-latest-payload-read — 2026-08-02

branch: fix/890-prune-latest-payload-read
diff_sha256: 51f6ff2db2c67f443d79e135238bbc051cc1f02f9298f25a199c96d88c40ca38
# One-commit branch, so `--staged-hash` equals the cumulative `origin/main...HEAD` hash. They diverge
# on a second commit; take it from `check_task_artifacts.py --base origin/main` if one is needed.

rounds: 3
# Round 3 was a scope-auditor FAIL on an amendment that has since been WITHDRAWN, not fixed: the
# handover was pulled out of this branch entirely, restoring the diff to byte-identical with the
# state all three reviewers passed. The hash above is that state. Detail in escalations.log.

## scope-auditor
VERDICT: PASS
risks_checked:
- Authority is real and present, checked against `escalations.log` rather than the contract's word:
  the CPO's "merged, do 890" is recorded for this branch, and the standing "Fix it and ensure that
  this will not happen again in the future" is recorded under #547. Both say what the contract says.
- The agent-executable argument is sound and not over-broad. §10 reserves API budget, history depth,
  run cadence and widening a task; this changes none of them, and a reduction in bytes read on
  identical semantics does not trip the cost gate. Round 1 correctly failed the first version, which
  declared the threshold and named no authority at all when the authority existed.
- Scope: both touched files are in `scope_paths` and only those are edited.
- The `league_code` move from f-string to query parameter is hardening inside a line already being
  rewritten, not an unrelated change riding along.
- The `impact_map`'s five call sites verified by independent grep; every caller expects dict-or-None
  and the return contract is unchanged.
- Appendix A6, assert-before-measure: the contract cites `bq query --dry_run` figures rather than
  intuition, and the measurement that settled the design is banked.

## data-engineer-reviewer
VERDICT: PASS
risks_checked:
- Snapshot class per call site, which is the correctness question. Every table actually read through
  this function is a complete-snapshot or single-row WRITE_TRUNCATE table, never a merge-on-write
  (`RAW_APIF_FIXTURE_DETAILS`, `RAW_APIF_PLAYERS`) or skip-if-present accumulation table, where
  "newest row only" would be wrong. Checked against `docs/data_contract.md`, not assumed.
- The race between the two queries: `docs/operations_guide.md` documents a single-writer
  `RAW_APIF_INGEST_LOCK` lease, so no concurrent writer can land a row between them in production.
- Ties on the newest timestamp: `LIMIT 1` after the equality filter preserves the old
  single-row-of-several behaviour, and the writers put one row per (league, run) anyway.
- NULL timestamps: traced both writers; `ingested_at` is always set from `datetime.now(timezone.utc)`
  and never left null, so a NULL `MAX` means genuinely zero rows, matching the documented contract.
- The timestamp parameter type is read from the schema and is correct for every table-creation path
  in this module. The `ingested_datetime` branch is dead code carried over unchanged, not new risk.
- Writers untouched: no `WRITE_TRUNCATE`, no write path in the diff, matching "writers: none".
- The extra call is a BigQuery job, not an API-Football HTTP call, so the ingest budget, retry logic
  and daily quota behaviour are unaffected.

## platform-reviewer
VERDICT: PASS
risks_checked:
- The test genuinely pins the shape, traced against both reversion scenarios. Reverting to
  `ORDER BY ... LIMIT 1` fails on the query count or the JSON decode; reverting to a subquery
  predicate keeps two round trips but fails the `ingested_at = @ts` and `SELECT MAX` assertions. It
  is not a happy-path assertion.
- The fake client matches the real `google-cloud-bigquery` 3.25.0 surface for everything the code
  under test calls: `schema`/`field_type`, `query(sql, job_config=...)`, `.result()`, `.to_arrow()`,
  and `ScalarQueryParameter.name`/`.type_`/`.value`.
- `_scalar` propagates a BigQuery exception uncaught, which matches how the rest of the module
  handles failure; no new inconsistency.
- `tests/test_fixtures_cache_skip.py` patches the name in `loads.fixtures`, so the internal rewrite
  is invisible to it and those tests still assert what they did.
- No mutable-default, closure-over-loop or shadowing bug: `_where(extra=None)` closes over
  `conditions` read-only and `params + [...]` builds a new list rather than mutating the one already
  handed to `_scalar`.
- The new test file is picked up by `pytest tests/` with no registration step, and no dependency or
  CI wiring changed.
- Delta: the empty-result case is now parametrised over both the real BigQuery shape (one row
  holding NULL) and a genuinely empty result. Both reach `None` through different branches of
  `_scalar`, and the test is not vacuous, because a regression that issued a second query would
  raise `IndexError` on the exhausted canned results rather than passing quietly.

## escalations
(none — the CPO's instruction was given directly in session and is recorded in `escalations.log`
and cited in `decisions_taken` rather than raised as a blinded question here.)
