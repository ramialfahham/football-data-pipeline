# Review — perf/ci-slim-build — 2026-06-25 (Slim CI: PR builds only changed models)

> G3 Lock artifact. Reviewers spawned cold (blinded) on the staged branch diff
> (`.claude/task/review_input.patch`). Required set for the staged paths
> (.github/workflows/ci-data-build.yml + contract.md): scope-auditor (always) +
> cto-reviewer (.github/workflows/** — PROTECTED guard path, reviewed on the opus floor).
> No analytics-engineer/data-engineer/bi-analyst/football-analytics (no dbt model, seed,
> ingestion, wireframe, or catalogue path touched).

diff_sha256: 73f7db255510309ef9c0e632e98b54be7d24d23138b940b0309638fd4ce5ae6f

## scope-auditor
VERDICT: PASS
risks_checked:
- Scope adherence: the diff touches ONLY `.github/workflows/ci-data-build.yml` (the sole
  scope_paths entry) plus the hashed contract.md — no out-of-scope drift.
- Protected-path discipline: `.github/workflows/**` is PROTECTED; the contract carries a
  `protected_override` naming the CPO approval ("A with Option 2", 2026-06-25) and the change
  is confined to that approved intent (slim CI, Option 2) — no smuggled changes.
- Freshness-exclude honoring (workflow `--select state:modified+ --exclude tag:freshness_check`
  vs selectors.yml): dbt honours `--exclude` with `--select` (only a named `--selector` drops
  it); selectors.yml documents the same rule; the freshness-tagged tests stay excluded on PR.
- Shared-warehouse dataset integrity (generate_schema_name.sql vs the CI profile): the macro
  returns the bare schema regardless of target, so CI and prod write the same datasets; the
  slim build rebuilds only touched models into the shared dataset and unchanged upstreams'
  ref()s resolve — no --defer needed, matching the contract's claim.
- §10 / DQ: no CPO-class decision taken silently — the slim-CI mechanism is the pre-authorized
  change; the full singular DQ suite still runs on every build; the isolation question is
  explicitly RESERVED, not folded in.

## cto-reviewer
VERDICT: PASS
risks_checked:
- Guard integrity / authorization (contract protected_override + routing `.github/workflows/**`
  → cto-reviewer): authorization present and correctly scoped to the one workflow file plus the
  hashed contract; no unquoted new mechanism.
- PR-vs-push gating completeness (ci-data-build.yml): the four build steps partition the three
  triggers cleanly — `pull_request` → compile-baseline + slim build; `push:main` and
  `workflow_dispatch` → full staging+downstream (`!= 'pull_request'`). Exact complements: exactly
  one build path per trigger. The terminal `gate` job and the `changes` path filter are untouched.
- Empty-selection no-op for model-free PRs (dbt 1.7 pinned): `dbt build --select state:modified+`
  on a PR that changes no dbt nodes matches nothing and exits 0 with a "nothing to do" warning
  (not an error); the full singular-test step still runs. Holds for this very (workflow-only) PR.
- Baseline compile prerequisites & working-directory: the `/tmp/main-src/dbt_project` subshell
  inherits the profile (~/.dbt, default profiles-dir) and runner-global WIF auth (done earlier),
  runs its own `dbt deps`, and `git -C "$GITHUB_WORKSPACE"` targets repo root (overriding
  working-directory: dbt_project). `git worktree add --detach FETCH_HEAD` after `fetch --depth=1`
  is a known-good shallow-clone pattern; `--target-path /tmp/main-state` matches the `--state` consumer.
- state:modified+ correctness on the shared warehouse with no defer: generate_schema_name returns
  the bare `+schema` regardless of target, so unchanged upstreams' ref()s resolve to existing prod
  tables; modified nodes + ALL descendants build; no missing-upstream case. The 3 incremental facts
  rebuild incrementally only when their lineage changed — identical to today; net prod churn decreases.
- Freshness exclusion + DQ gate preserved: slim path uses CLI `--exclude tag:freshness_check` with
  `--select` (honoured); the full `test_type:singular` DQ suite is unchanged and runs on every trigger.
- Scheduled prod run isolation: dbt-scheduled.yml is not in the diff; it still runs the full `dbt
  build` after 04:00 ingestion (freshness included); the slim logic lives entirely in the
  ci-data-build `pull_request` branch and cannot reach the scheduled refresh. No permission/credential
  change (permissions block unchanged).

## escalations
(none)
