# Task contract — serialize the prod-writing workflows (#667)

> Written on a CLEAN tree (branch fix/667-prod-writer-concurrency off main @ b96cf76).
> Follow-up to #668 (env isolation): closes the cross-workflow PROD-write race deferred there.
> CPO-directed this conversation 2026-07-08 ("go ahead" on issue #667).

objective: >
  Give the three PROD-writing workflows one shared GitHub Actions concurrency group so they can no longer write
  the bare prod datasets (`marts`/`core`/`staging`/`intermediate`) concurrently and hit BigQuery
  `Could not serialize access` on the incremental `fct_fixture_*` MERGE targets. This is the pre-existing race
  #668 isolated non-prod from but explicitly deferred (issue #667). PR CI builds are unaffected — they keep their
  own `ci`-scoped group and their `ci_*` datasets.
refs: #667 (this task); #668 (env isolation that surfaced + deferred it); [[project-dbt-shared-ci-prod-datasets]].

protected_override: >
  CPO-authorized 2026-07-08 (this conversation, "go ahead" on #667) to edit the PROTECTED `.github/workflows/`
  guard paths in scope — ci-data-build.yml, dbt-scheduled.yml, pages-match-preview.yml. Override scope:
  `concurrency:` groups ONLY. No change to triggers, path filters, the terminal `gate` job, required-check logic,
  the ingest skip-if-exists, dbt targets/flags, or any build step.

scope_paths:
  - .github/workflows/ci-data-build.yml
  - .github/workflows/dbt-scheduled.yml
  - .github/workflows/pages-match-preview.yml
  - .claude/task/**

impact_map: >
  Adds a single shared repo-wide concurrency group `prod-warehouse-write` (cancel-in-progress:false) across the
  three prod-writers, so at most one prod dbt run executes at a time. Edits: (1) ci-data-build's `data-build` job
  group becomes `${{ pull_request && 'ci-data-build-write-ci' || 'prod-warehouse-write' }}` — the PR arm keeps its
  own ci group (PR isolation unchanged), the push/dispatch (prod) arm joins the shared group. (2) dbt-scheduled
  gains a workflow-level `prod-warehouse-write` group (its single nightly job is entirely a prod write).
  (3) pages-match-preview gains a JOB-level `prod-warehouse-write` group on the `build` job only — NOT workflow
  level — so its dbt writes serialise with the others while its existing workflow-level `pages-match-preview` group
  and its separate `deploy` job are untouched (the Pages deploy is not blocked behind unrelated dbt runs).
  GitHub treats a group name identically whether declared at workflow or job level, so the three queue as one.
  NO change to triggers, targets, build/seed/test steps, path filters, permissions, secrets, or the `gate` job —
  purely a scheduling (serialization) change. Risk surface: (1) over-serialization — the pages `build` job's
  non-dbt tail (export/assemble/upload) also queues behind other prod writers; acceptable, these workflows run at
  distinct times (04:00 nightly / 07:30 pages / on-merge) so real contention is rare and correctness > a few
  minutes of queueing. (2) cancel-in-progress:false is required so a queued run never cancels an in-flight prod
  build mid-MERGE.

decisions_taken: >
  Shared group name `prod-warehouse-write`; `cancel-in-progress: false`. pages joins via JOB-level concurrency on
  `build` (deliberate — protects the Pages deploy from being serialised behind dbt). ci-data-build's PR arm stays
  on its own `ci-data-build-write-ci` group (PR builds must NOT serialise behind prod). All within the CPO "go
  ahead" for #667.

decisions_reserved:
  - Splitting the pages `build` job so ONLY the dbt steps (not export/assemble/upload) serialise — not worth the
    workflow restructure now; the tail is short and pages is low-frequency. Revisit only if queueing bites.

done_when:
  - ci-data-build data-build job: prod arm on `prod-warehouse-write`, PR arm on `ci-data-build-write-ci`.
  - dbt-scheduled carries a workflow-level `prod-warehouse-write` group.
  - pages-match-preview `build` job carries a job-level `prod-warehouse-write` group; workflow-level group + deploy job untouched.
  - YAML valid; scope-auditor + cto-reviewer PASS; review.md diff_sha256 binds; CPO merges; #667 closed.

amendments: (none)
