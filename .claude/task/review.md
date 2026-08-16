# Review — fix/75-batch-fixtures-896-guard — 2026-08-16

diff_sha256: af1c8e6098330e575c26776ed128b82374fb825f28239a187efc2dd62772f8a1

rounds: 2

## scope-auditor
VERDICT: PASS
risks_checked:
- Diff file set vs `scope_paths`: `batch_fixtures.py`, `tests/test_incomplete_fetch_no_supersede.py`, `docs/data_contract.md`, `contract.md`, `escalations.log`. `docs/data_contract.md` was added mid-task via a recorded `amendments:` entry citing Class-1 rule 5, raised by data-engineer-reviewer round 1 — not a silent widening.
- No dbt file, no model, no seed, no CI file in the diff. The change is one loader plus its guard test plus the raw contract doc.
- `decisions_reserved` is honest and not used to launder an executed decision: the standing orphan is explicitly NOT cleared, and the "may a complete-but-smaller response supersede" question is left to the CPO with the reason (#896's 2026-08-03 ruling says the opposite today).
- The four rejected proposals are recorded in `escalations.log` with why each was wrong, rather than quietly dropped. `_STATS_RETRY_DAYS` untouched.
- Credential sweep of the whole diff: none.

## data-engineer-reviewer
VERDICT: PASS
risks_checked:
- Traced all four paths in `_fetch_and_persist_batch`: incomplete → return before any write; empty-but-complete → return before the delete block; retry returned → delete then re-insert from the same response (net one row); retry omitted → excluded from `retries_in_batch` and absent from the insert, old row untouched. The docstring claim that delete and insert stay paired, so no second row is created, holds on every path.
- ROUND 1 FINDING 1 FIXED: `docs/data_contract.md` now says the row is the latest COMPLETE payload, names the #896 guard, and matches the traced code. No contradiction with `layering.md` or the RAW_APIF_PLAYERS section.
- ROUND 1 FINDING 2 FIXED: `returned_ids` is now an explicit loop with `isinstance` guards, chained `.get()`, and `try/except (TypeError, ValueError)`, matching `_extract_fixture_id`'s shape.
- FABRICATED JUSTIFICATION CORRECTED: round 1 observed the guard cannot produce a duplicate row. The builder's "transient two rows" claim in both the module docstring and the LOGICAL_OR comment was wrong and has been rewritten. The LOGICAL_OR now rests on the true reasons — BigQuery promises no row order for a per-row dict read, and `_insert_fixture_rows` does not dedup a response repeating an id (a pre-existing risk, not introduced here). It is a no-op for the single-row case.
- Guard placement: `result_is_complete(data)` is called immediately after `fetch_json` and before any delete, satisfying its documented latch requirement and matching `coaches.py`.
- Whole-batch discard delays new fixtures by one run rather than losing them — the accepted `coaches`/`squads` precedent.
- Both new tests hand-traced as genuinely red-then-green, not vacuous: reverting the guard deletes both ids; reverting the `returned_ids` filter deletes `[111, 222]`.
- No `WRITE_TRUNCATE` introduced; still `WRITE_APPEND` with DELETE+INSERT, merge-on-write and the raw cost bound (#33 item 8) preserved; growth still bounded to retried fixtures.
- No cadence, fanout or history-window change; `_STATS_RETRY_DAYS` unchanged and flagged open in `decisions_reserved`.

## escalations
- question: May a COMPLETE provider response carrying strictly less data than what is stored supersede it? Measured: 5 fixtures, 29 events, and the provider now returns 17 events for 1564795 where the fact holds 27.
  CPO ANSWER: NOT TAKEN — deliberately left open. #896's ruling of 2026-08-03 decides the ambiguous case the other way ("an empty response with no error counts as COMPLETE ... indistinguishable"), so changing it reverses part of that ruling and is the CPO's call. Recorded in `escalations.log` and in `decisions_reserved`; this MR does not touch it.
