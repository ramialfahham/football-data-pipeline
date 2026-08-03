# Review — fix/896-incomplete-fetch-must-not-supersede — 2026-08-03

branch: fix/896-incomplete-fetch-must-not-supersede
diff_sha256: 28840a4b2a50cbf4f058af772424f096790637b212cd0b9ad785d69524a5edd0

rounds: 2
# Required reviewer set computed from `.claude/review_routing.json` for the staged paths:
# `ingestion/**` routes `data-engineer-reviewer`, `tests/**` routes `platform-reviewer`, and
# `scope-auditor` is always-on. The commit is NOT artifact-exempt, because `contract.md` is never
# artifact-exempt (F10/#409).
#
# ROUND 1 FAILED. `data-engineer-reviewer` found that carrying the completeness signal as a KEY on
# the dict returned by `fetch_merged_paged` would leak it into four raw tables (RAW_APIF_STANDINGS,
# RAW_APIF_TEAMS, RAW_APIF_INJURIES, RAW_APIF_FIXTURES_NEXT) via `_merge_merged_paged` and the
# manual envelope comprehensions, with a value frozen at the first iteration of a multi-season
# merge. The signal was redesigned into a function, `http_client.result_is_complete`, so no returned
# dict gains a key. `impact_map` was extended on a clean tree to trace the shared helper's other
# callers; `scope_paths` unchanged. Full record in `escalations.log`. Verdicts below are round 2.

## scope-auditor
VERDICT: PASS
risks_checked:
- Amendment narrowness: the extended `impact_map` only documents blast radius that was always
  present, widens no permission and takes no new decision. `scope_paths` unchanged.
- Redesign recording: the round 1 failure and its resolution are both recorded in
  `escalations.log`, and the underlying CPO ruling on trigger-signal (error versus emptiness) is in
  `decisions_taken` with its measured price.
- Threshold accuracy after the redesign: NEW MECHANISM "none" rests on the CPO's explicit
  classification of this as an EXTENSION of the existing `quota_cut` PARTIAL handling.
  `result_is_complete` is a new function but not a new mechanism under §10. RECURRING COST "none"
  holds: call count, daily quota draw and run duration are unchanged, and the rejected alternative's
  +42 min/run figure is recorded so it is not re-litigated.
- Scope boundary: all seven changed files fall within `scope_paths`; no protected path touched.
- Decisions reserved: all three (PR 3 threshold, the pre-existing `meta=None` hazard, page-cap
  behaviour) are listed and appropriate.
- No credential or secret in the diff.

## data-engineer-reviewer
VERDICT: PASS
risks_checked:
- Leak closure verified at the SOURCE, not just the call site: `fetch_merged_paged` builds `out`
  from provider envelope fields plus `errors`/`response`/`results`/`paging` only, in both branches.
  No completeness key is ever set. `result_is_complete` reads `data` and never writes into it, and
  the value reaches only a local control-flow gate in `squads.py`, never the written row. The four
  sibling loaders named in round 1 are unaffected because the leak was in the shared helper's return
  shape, now fixed at the one place all of them read from. `TestReturnedKeySetIsStable` pins the
  exact key set for both branches, so a reintroduction fails CI rather than relying on review.
- Semantics versus the pre-existing `quota_cut`: these are independent, non-conflicting signals.
  `quota_cut` still only drives the end-of-run PARTIAL log line. The four measured incidents were
  per-minute rate limits, which arrive as HTTP 200 with a non-empty body-level `errors` and are
  caught by the error half; the quota half exists for genuine daily exhaustion, where `fetch_json`
  short-circuits to an empty body with no error at all. The paginated loop aggregates `merged_errors`
  across all pages, so the APD/463 shape (limit on page 2 of 3) still surfaces in the final errors.
- Call-ordering hazard: completeness is computed immediately after the fetch returns, before the
  only intervening call (`append_api_errors`, which does no I/O). The pipeline is single-threaded
  and single-process and holds an ingest lock, so the process-global flag cannot change in between.
- The guard holds: an incomplete fetch withholds both the row append and the `written_keys` append,
  so `_delete_superseded_player_rows` cannot delete for an incomplete key and no row is written that
  would poison `captured_player_team_seasons`.
- General merits: `players_response_for_team` has exactly one caller, so the tuple-return change
  breaks nothing silently. No raw schema, column or naming change. No cost or scope knob touched.

## platform-reviewer
VERDICT: PASS
risks_checked:
- `TestReturnedKeySetIsStable` is not vacuous: verified against the real key-building logic, and the
  reintroduction check was actually observed to fail with the extra key present.
- The provider-meta pass-through test drives synthetic `fetch_json` output and asserts against the
  real pass-through mechanism, so it cannot spuriously break when the provider adds an envelope
  field, and it is not an over-constraint.
- `_http_quota_exhausted` isolation across the now-larger set of touched classes: every mutation
  path is covered, either by `monkeypatch.setattr` or by the autouse reset fixture, including the
  one test that sets the flag by bare assignment inside a closure, because the fixture teardown
  resets unconditionally.
- The signature change from `list` to `tuple[list, bool]` has exactly one production caller, which
  is correctly updated.
- No leftovers from the rejected key-on-dict design: no stale comment, dead variable or docstring
  refers to it; the only remaining mentions warn against reintroducing it.
- Re-run and interruption safety: withholding the write and the key leaves the prior row untouched
  and the team-season uncaptured, so a retried run re-fetches it. Self-healing, no half-applied
  state.

## escalations
(none)
