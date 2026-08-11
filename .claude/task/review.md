# Review — perf/33-item14-refetch-cadence — 2026-08-10

diff_sha256: 16ef2e2f5d755991a4a03a23311f385eb4c9d791448369b4b5af4038510df317

rounds: 4

rounds_cap_override: CPO authorised explicitly — "run round 4" — so scope-auditor's round-3
finding could be fixed and re-verified rather than accepted on the builder's word. The cap
exists to stop grinding; here the extra round was paid for by a real defect the reviewer found.

<!--
REBASED onto main after #39 Stage 2 (!30) merged, 2026-08-10. The four `.claude/task/*` files
conflicted, as every pair of concurrent branches in this repo does: `contract.md`, `review.md`
and `review_input.patch` were taken from THIS branch (they describe THIS task), while
`escalations.log` was UNIONED — it is append-only history and both Stage 2's entry and item
14's had to survive. Verified: both are present, no conflict markers remain.

`diff_sha256` was rebound with `scripts/check_task_artifacts.py --base main`, NOT
`--staged-hash`. On a rebased branch the staged hash covers only the increment while CI
recomputes over the whole branch, so the two diverge and the local number would false-green.

No reviewer verdict below was re-run for the rebase: no code, test or contract line changed —
only the base commit and the three artifacts above. The rebase did, however, bring the two
halves of this change together for the first time, and that was verified rather than assumed:
`scripts/check_raw_freshness.py` (from !30) now reads item 14's raised thresholds, 240h error
instead of 54h. Without item 14's `sources.yml` edit the sentinel would have paged daily the
moment the cadence went live.
-->

<!-- Post-rebase verification: pytest 764 passed / 1 skipped (main after !30 is 751), ruff
     clean, no conflict markers, both escalations entries intact. -->


<!--
Round history. Every FAIL was the builder's, and the first two were live bugs, not paperwork:
  r1  analytics-engineer FAIL  (stagger broke the ruled cadence; COACHES mislabelled)
  r2  data-engineer FAIL       (contract cited a file that lives on an unmerged branch)
  r3  analytics PASS · data-engineer PASS · platform PASS · scope-auditor FAIL
  r4  scope-auditor PASS

Verdicts below are each reviewer's LAST. analytics/data-engineer/platform passed at round 3
against a diff that differs from this one by exactly one addition — the 2026-08-10
`escalations.log` entry that cured scope-auditor's finding. No code, test or contract line
changed after their pass. Stated rather than glossed, because the hash binds all four to the
final diff and only scope-auditor saw the last delta.
-->

## scope-auditor
VERDICT: PASS
risks_checked:
- Round-3 finding 1 (the CPO ruling and both derived consequences claimed in `contract.md` but absent from `escalations.log`): remedied — verbatim ruling quote and explicit builder-derived flagging with stated costs now recorded at `escalations.log:1864-1914`, in the format this repo has used for every other accepted ruling.
- Round-3 finding 2 (the `orchestrator.py` amendment citing an unrecorded "CPO-approved plan"): remedied — the same entry records the scope-amendment authority and the specific plan content at `escalations.log:1916-1920`, outside the artifact it authorises.
- Circularity check, because a second self-authored copy could be no better than the first: compared this entry's evidentiary format against ~10 other accepted ruling records in the same log (lines 337, 1015, 1172, 1306, 1359, 1840). Same "verbatim, in-thread" convention throughout — line 250 explicitly flags that its quotes cannot be verified from repo contents by a cold reviewer and was accepted. This meets the established bar, not a lower one invented for this task.
- Premise check re-verified INDEPENDENTLY rather than taken from the contract: grepped `ingestion/api_football/loads/` for the five named skip-logic patterns; `transfers.py` and `coaches.py` are absent from the matches, consistent with "neither loader has ever had skip-if-present logic".
- Confirmed no code, test or `contract.md` line changed in this delta — only `escalations.log` — so no new surface required re-audit.
- (r3, still standing) Scope conformance: every changed file maps to a `scope_paths` entry, including the amended `orchestrator.py`.
- (r3) The stagger fix verified not reintroduced: `should_refetch`'s safety net (`age_days >= interval_days`) precedes the slot check, so every league gets the full ruled interval.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Threshold arithmetic against a genuine 7-day cadence: `warn 8d` gives one day of slack before warning, `error 10d` tolerates one fully missed cycle before erroring — and the relationship is pinned by `test_freshness_thresholds_exceed_the_cadence` so cadence and thresholds cannot drift apart.
- Confinement of the relaxation: only `raw_apif_coaches` and `raw_apif_transfers` moved; the other nine sources in `sources.yml` are untouched, and `test_the_nightly_sources_keep_their_tight_thresholds` guards that boundary going forward.
- No league identifier hardcoded anywhere; the change is table-scoped, not competition-scoped.
- Downstream: no SQL, model or grain changed. The `impact_map`'s pasted `dbt ls` output (`stg_apif__coaches/coach_career/transfers` → `base_apif__*` → `dim_coach`, `dim_coach_team_mapping`, `fct_transfer`) matches an independent grep of `dbt_project/models`; nothing further downstream references these, so "blast_radius: NONE on 9 models" holds.
- Round-1 finding 1 (the stagger permanently shortening the interval so most leagues re-fetched daily) — verified fixed against the new slot arithmetic.
- Round-1 finding 2 (`RAW_APIF_COACHES` wrongly called merge-on-write in four places) — verified corrected against `data_contract.md`, `stg_apif__coaches.sql` and `loads/coaches.py:83`, which confirms `append=True` with no delete call.

## data-engineer-reviewer
VERDICT: PASS
risks_checked:
- Cadence arithmetic in `refetch.py::should_refetch`: traced the slot modulo against the safety net (`age_days >= interval_days`) and the same-day floor (`age_days < 1`). Steady-state gaps are exactly 7 days per league by a pigeonhole argument — any 7 consecutive days contain exactly one slot day for a given offset. A missed run self-heals via the safety net. The only transient is a possibly-shorter first interval after a `None`-triggered first ingest: one-time, and in the safe direction (an extra fetch, never a skip).
- Hoisting placement in `orchestrator.py`: `latest_ingest_per_league` called exactly once per table, after `acquire_ingest_lock` and before the per-competition loop; both consumers receive the same pre-computed dict. No O(competitions²) reintroduced, and no coaches/transfers write happens earlier in the run that this read could miss.
- Failure direction: `latest_ingest_per_league` catches all exceptions and returns `{}`; `.get()` yields `None`; `should_refetch(..., None, ...)` returns True. A failed read makes every league DUE, never silently skipped.
- Write modes confirmed at source: `loads/coaches.py:83` append-only with no `delete_superseded_league_rows`; `loads/transfers.py:88` merge-on-write via that call. Matches the corrected comments.
- The `new_data` gate: `ctx.tables_loaded` is incremented by loaders that still run unconditionally every night (fixtures, standings, teams, injuries), so a coaches/transfers skip cannot by itself drive `new_data` false and suppress the warehouse build.
- Call-site completeness: `run_cheap_phases` and `run_transfers_for_competition` are called only from `orchestrator.py`; both updated, no stale caller left behind.
- Round-2 finding (the contract citing `scripts/check_raw_freshness.py` as present fact when it lives on unmerged !30) — verified corrected; the contract now states the consumer is not in this diff and that the change is inert either way.

## platform-reviewer
VERDICT: PASS
risks_checked:
- Decoration hunt across all new tests: for each, identified the single production edit that flips it red — reinstating `due_after = interval - offset` (the year-long simulation fails for 6 of 8 leagues), removing the `return` after a skip (the no-write test fails), making a never-ingested league skip (three tests fail), widening `REFETCH_INTERVAL_DAYS` without touching `sources.yml` (the threshold-drift guard fails). None vacuous.
- `test_a_skipped_league_writes_nothing_at_all` exercises the real `run_transfers_for_competition` path with the loader replaced by a recorder, asserting zero calls rather than "a call with less data" — the assertion that actually guards against the #37 shape on a merge-on-write table.
- `test_the_logged_next_due_date_is_the_day_it_actually_refetches`: `next_due` and `should_refetch` are pinned to agree, so the skip log cannot report a date the scheduler will not honour. A log that lies during an incident is worse than none.
- The stagger's stability: `md5` rather than the builtin `hash()`, which Python salts per process — a per-run-varying offset would smear the cadence. Pinned by test.
- Env override reuses the existing `API_FOOTBALL_INGEST_FORCE_FULL` rather than introducing a second flag; verified it bypasses the cadence.
- Skip visibility: `_skipped_phase` logs age and next due date, so a silently-stopped phase is distinguishable from a deliberately skipped one in the nightly log.

## escalations
(none)
