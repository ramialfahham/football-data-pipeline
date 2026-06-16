# Review — feat/squad-capture-finished-comps — 2026-06-16

diff_sha256: bb22215bf9dca1c246344877bcba12ca5a63147f9edbbf98a1ba7bf8c62313be

Cold review over three rounds (scope-auditor + data-engineer-reviewer + cto-reviewer). The first
two rounds surfaced two real defects, both fixed in code and re-verified:
1. `captured_team_seasons` queried a bare/unqualified BigQuery table → it would error on every run,
   the broad `except` would swallow it, and the per-season dedup would be silently inoperative
   (re-fetching every finished comp daily). Fixed to a fully-qualified `project.dataset` reference
   (matching `_fq` in player_universe.py), validated on real BigQuery (query executes; JSON paths
   extract real team_ids), and locked by a regression test.
2. The catch-up could persist a PARTIAL squad row on quota exhaustion, which `stg_apif__squads`
   (latest snapshot per `league_code`) would silently truncate. Fixed: catch-up writes are atomic
   per competition (`require_complete=True` discards a partial; the whole comp re-captures next run).
Full test suite: 273 passed.

## scope-auditor
VERDICT: PASS
risks_checked:
- Every edited path is inside the contract `scope_paths`; the `escalations.log` edit is a
  `.claude/task/**` bookkeeping artifact (edit-gate-exempt, hash-excluded), not scope drift; no
  staging/dbt file is touched (no scope creep beyond the ingestion-only contract).
- The CPO authority for the catch-up (a new mechanism) is now traceable: `escalations.log` carries a
  2026-06-16 entry recording the directives the contract's `decisions_taken` cite, plus the two
  review-cycle §10 rulings — no §10 decision is taken silently.

## data-engineer-reviewer
VERDICT: ESCALATE
risks_checked:
- The round-1 unqualified-table defect is fixed and verified (fully-qualified read; real-BQ
  execution + JSON-path extraction confirmed); the round-2 partial-write / staging silent-loss is
  fixed (atomic-per-comp catch-up write); no silent-loss path remains under the atomic design.
- Quota/cost (no extra fixture calls; team lists reused from the poll phase), idempotency
  (per-(team,season) dedup), and per-comp failure isolation re-confirmed safe.
- Two residual findings are §10-class (a rule-classification call + a scope call); per decision
  rights the builder did not self-rule — both were put to the CPO in plain language with options and
  a recommendation, and answered:
- question (Q1 — rule classification): Does the 2026-06-12 sample-fixtures rule (offline tests vs
  committed `tests/fixtures/apif/` payloads) apply to this diff? It adds no new response-parsing —
  `run_poll_phases` captures the `team_ids` that `fetch_merge_and_persist_fixtures` already returns
  (`run_cheap_phases` destructures the same return), and `captured_team_seasons` extracts JSON in
  BigQuery SQL (validated on real rows); the `tests/fixtures/apif/` harness does not exist (audit
  F21, pre-existing debt).
  CPO ANSWER: (2026-06-16) the rule does NOT apply here — proceed; do not block this change on
  building the absent fixtures harness. (Recorded in escalations.log.)
- question (Q2 — scope/design): Accept the in-scope atomic-discard for the catch-up's
  quota-vs-completeness trade-off, or expand scope to make `stg_apif__squads` UNION ALL snapshots so
  partials accumulate safely?
  CPO ANSWER: (2026-06-16) ACCEPT the atomic discard (discard the partial, re-capture the whole comp
  next run; logged + eventually completes — comps are ≤~100 teams vs 75k/day). The
  `stg_apif__squads` UNION-ALL change is deferred to when squads staging is consumed downstream —
  not this PR. (Recorded in escalations.log.)

## cto-reviewer
VERDICT: PASS
risks_checked:
- The new `captured_team_seasons` / `require_complete` tests genuinely exercise the discard-vs-write
  branch and guard the qualified-table fix; monkeypatch targets the correct module objects;
  deterministic (sorted team iteration); no network or BigQuery at import or run time.
- `pytest tests/` passes under the CI gate with no new dependencies (`monkeypatch` and
  `types.SimpleNamespace` are stdlib); re-run safety and fail-open behaviour confirmed. Two
  non-blocking notes accepted: the pre-loop quota-exhaustion path logs nothing under
  `require_complete`, and the in-season partial-write test asserts that a write occurred but not its
  payload content.

## escalations
See the data-engineer-reviewer section (Q1, Q2) — both CPO-answered 2026-06-16 and recorded in
`.claude/task/escalations.log`.
