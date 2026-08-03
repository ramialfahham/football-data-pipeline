# Review — fix/898-surface-dropped-calls — 2026-08-03

branch: fix/898-surface-dropped-calls
diff_sha256: ebc5c5b35770c640772f0c4221e3b82a754b21cc4892f91f54456c0e6a9ad99d

rounds: 2
# Required reviewer set from `.claude/review_routing.json` for the staged paths: `ingestion/**`
# routes `data-engineer-reviewer`, `tests/**` routes `platform-reviewer`, and `scope-auditor` is
# always-on. NOT artifact-exempt, because `contract.md` is never artifact-exempt (F10/#409).
#
# ROUND 1 FAILED TWICE, on two independent defects found by the two specialists:
#  A. `data-engineer-reviewer` — the counter lived in `append_api_errors` and double-counted
#     `fixtures`, because `loads/fixtures.py` calls it twice against overlapping data (per season at
#     :163, then on the accumulated envelope at :183, which `_merge_merged_paged` carries the
#     earlier errors into). Fixed by moving counting into `fetch_json`, once per call whose final
#     attempt was still rejected, keyed by API path. `append_api_errors` is now unchanged.
#  B. `platform-reviewer` — the new gate was ORed into the orchestrator's exit condition and so
#     honoured neither `report["skipped"]` nor `fail_on_incomplete()`, unlike the existing
#     `stagnant_statistics` signal. Fixed by moving it inside `evaluate_completeness_outcome`.
# The contract was amended on a clean tree to admit one test file whose exact-equality assertion the
# approved change breaks. Full record in `escalations.log`. Verdicts below are round 2.

## scope-auditor
VERDICT: PASS
risks_checked:
- Amendment authority: the CPO approved a change that adds a key to `evaluate_completeness_outcome`'s
  returned dict, a test asserts that dict by exact equality, so the test must change and the file
  must be in scope. Inference grounded in a recorded CPO decision, not an invented rule.
- Scope: only `tests/test_completeness_outcome_and_summary.py` was added to `scope_paths`. The
  `impact_map` correction removes a false claim about `append_api_errors` rather than widening
  permission. No new decision is taken; threshold policy, N and the freshness trade are unchanged.
- NEW MECHANISM still "none" after the redesign: the gate, the 503 to exit 3 path, the snapshot
  table and the prior-versus-current comparison all pre-existed, and the retry is a fourth branch in
  an existing loop.
- RECURRING COST still accurate: one extra HTTP call per rate-limited call, one extra key in an
  existing payload, no change to endpoints, quota draw or pacing.
- Guard preservation: the exact-equality assertion was EXTENDED to include the new key, not relaxed
  to a subset, so a future signal still cannot be added there unnoticed.
- Both round 1 defects verified fixed at the root, and the per-minute detector never sets
  `_http_quota_exhausted`.

## data-engineer-reviewer
VERDICT: PASS
risks_checked:
- Round 1 Fail A fixed at the root: `append_api_errors` is unchanged from main, confirmed by the
  diff touching no hunk in it and by grep over all 16 call sites, including the two overlapping
  calls in `loads/fixtures.py`. Counting lives solely in `record_minute_rate_limit`, called from
  exactly one site. A caller reporting the same drop twice can no longer inflate the tally, because
  nothing at that layer increments it.
- Every path through `fetch_json` traced by hand: the `_http_quota_exhausted` early return (no HTTP,
  no count), a daily-limit body (returns before the minute branch), a minute limit on attempt 0
  (sleeps and continues, no count), a minute limit surviving to attempt 1 (counted exactly once), a
  retry that comes back clean (no count), and a clean first response (no count). A 429 or 5xx retry
  landing on attempt 1 with a body-level minute limit is still counted once, because the two-attempt
  budget is shared rather than additive.
- Round 1 Fail B verified structurally rather than from the contract's word: the signal is computed
  inside `evaluate_completeness_outcome`, before its single `fail_on_incomplete()` gate and after
  its `report["skipped"]` early return, and the orchestrator's exit condition is back to plain
  `if outcome["hard_fail"]` with no separate OR.
- Visibility versus failure separation: the raw per-run counts are read straight from
  `minute_rate_limit_counts()` and print regardless of either kill-switch; only the stagnation note
  and the fail path read the gated value. A skipped or overridden run still shows the drops and
  never exits 3.
- Read-before-write ordering: prior counts are loaded before this run's are persisted, so the
  comparison is prior-versus-current and not self-versus-self, and no HTTP call happens in between.
- Endpoint keys are stable literals: every `fetch_json` / `fetch_merged_paged` call site passes a
  fixed path string, never interpolated with team or player ids, so the dict keys compare correctly
  run over run.
- The two detectors do not cross-match in either direction against the real provider strings, and
  the per-minute one never touches `_http_quota_exhausted`.
- Downstream and scheduler claims verified rather than taken on faith: no dbt or script reference to
  the snapshot table, and every post-ingest workflow step is gated on the ingest step succeeding.

## platform-reviewer
VERDICT: PASS
risks_checked:
- Both kill-switches now gate the signal from inside `evaluate_completeness_outcome`, and no
  separate ORed variable survives in the orchestrator. Pinned by five tests that call the function
  directly and would raise TypeError against the round 1 code, so this is genuine regression
  coverage rather than happy-path.
- Visibility preserved under both switches: the "DROPPED n call(s)" note is built from counts
  computed independently of the report and the override, so it prints on every run.
- The exact-equality assertion was extended in place, not relaxed to a subset or a containment
  check. Confirmed by reading the literal.
- Counter fix confirmed at source: `record_minute_rate_limit` is called from exactly one place, only
  on the final attempt, and `append_api_errors` is byte-for-byte unchanged.
- Test-state isolation: the counter is touched only by the new test file, which resets it before and
  after every test. Every other test file that exercises `fetch_json` monkeypatches it at a higher
  import site, so the real counter is never reached outside the file that manages it.
- Swept for leftovers of both rejected designs: no counting re-added to `append_api_errors`, no
  stray `stagnant_dropped` local, dead import or commented-out OR condition.
- Re-run safety: the counter resets at the top of every invocation, and the prior read precedes the
  persist, mirroring the existing `stagnant_statistics` pattern with no new failure mode.

## escalations
(none)
