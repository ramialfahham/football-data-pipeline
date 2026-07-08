# Task contract — warehouse environment isolation (prod / CI / dev)

> Written on a CLEAN tree (branch chore/dbt-warehouse-env-isolation off main @ f35b99f).
> Plan floating-finding-deer.md CPO-approved 2026-07-07 via ExitPlanMode (Option 2, full isolation).

objective: >
  Isolate the dbt warehouse into three environments so non-prod builds (PR CI, local laptop) can no longer write
  the canonical datasets the live site reads. Mechanism: target-name-derived dataset prefix in
  `generate_schema_name` — `prod` writes bare `marts`/`core`/`staging`/`intermediate` (unchanged; the export reads
  these), every other target is auto-prefixed (`ci_*`, `dev_*`). The CI slim build defers unchanged upstreams to
  prod; the three main/schedule workflows pin explicit `--target`. Fixes the shared-dataset clobber
  (`mart_player_momentum`, 2026-07-06) and the singular-DQ false-fails that run against half-mutated shared state.
refs: plan floating-finding-deer.md (CPO-approved 2026-07-07); [[project-dbt-shared-ci-prod-datasets]] diagnosis.

protected_override: >
  CPO-authorized 2026-07-07 (this conversation, explicit "yes") to edit the PROTECTED `.github/workflows/` guard
  paths in scope — ci-data-build.yml, dbt-scheduled.yml, pages-match-preview.yml. Override scope: the dbt
  `--target` / `--defer` / `--favor-state` flags and the profile heredocs; the per-event `dbt seed` target split;
  and a job-level `concurrency:` guard on ci-data-build's data-build job (the last two are reviewer-surfaced
  remediation WITHIN this task — CPO-approved 2026-07-08, see amendments). The guards' governance BEHAVIOUR is
  otherwise unchanged — no edit to path filters, the terminal `gate` job, required-check logic, or the ingest
  skip-if-exists. Basis: approved plan floating-finding-deer.md.

scope_paths:
  - dbt_project/macros/generate_schema_name.sql
  - dbt_project/dbt_project.yml
  - dbt_project/profiles.example.yml
  - .github/workflows/ci-data-build.yml
  - .github/workflows/dbt-scheduled.yml
  - .github/workflows/pages-match-preview.yml
  - docs/operations_guide.md
  - dbt_project/docs/layering.md
  - .claude/task/**

impact_map: >
  STRUCTURAL — changes target-schema resolution for EVERY model. Under target `prod` (nightly, main-push, Pages)
  datasets stay bare → ZERO change to what `scripts/export_*.py` reads and NO prod data migration (prod already IS
  today's shared state). Under `ci` models land in new `ci_*` datasets; under `dev`, `dev_*`. base + seeds keep
  riding `target.schema` (the profile `dataset`) — mechanism unchanged, already per-env. Workflow edits:
  ci-data-build PR path gains `--defer --favor-state` against a baseline manifest compiled with the PROD target
  plus `--target ci`; the push path adds `--target prod`; the `dbt seed` AND DQ steps are split by event (PR =
  ci+defer, push = prod) so the push path seeds the same prod dataset its build reads (the `staging`/`downstream`
  selectors exclude seeds). dbt-scheduled + pages-match-preview pin `--target prod`. Export scripts, model SQL,
  seeds, the registry and sync_dbt_vars are untouched — no metric/number/grain moves. Risk surface: (1) the defer
  baseline MUST compile with the prod target or deferred refs mis-resolve to `ci_*`; (2) a shared `ci_*` dataset
  can hold stale tables from prior PRs — neutralised by `--favor-state` forcing unselected refs to prod; (3) the
  CI service account (WIF) must be able to create `ci_*` datasets — same project and same permission set it
  already uses to write `marts`/`core` today; (4) two concurrent PR builds share the one `ci_*` dataset and the
  three incremental core facts (fct_fixture_*) compile to BigQuery MERGE (serialize-access race) — mitigated by a
  fixed-group `concurrency:` guard queueing PR data-builds.

decisions_taken: >
  All CPO-locked in the approving chat 2026-07-07: Option 2 (full dev + CI + prod isolation); one shared `ci_*`
  dataset (not per-PR ephemeral); naming = prod bare / `ci_` / `dev_` (single `dev_`, solo repo — not per-user).
  Snapshots are dormant (no `.sql` under dbt_project/snapshots/) → documentation note only, no snapshot code.

decisions_reserved:
  - `ci_*` dataset default-table-expiration/TTL — optional best-practice follow-up, not this PR.
  - Per-user dev prefixes — not needed for a solo repo.
  - Target-aware `target_schema` for any FUTURE snapshot — noted in dbt_project.yml, built when a snapshot lands.
  - Cross-workflow PROD-write serialization (issue #667) — the three prod-writers (dbt-scheduled nightly,
    ci-data-build main-push, pages-match-preview) share no concurrency group, so two could write the bare prod
    datasets concurrently (e.g. a merge near the 04:00 UTC cron) and hit the same `fct_fixture_*` MERGE
    serialize-access race. PRE-EXISTING — this PR neither introduces nor worsens it (it only pulls non-prod builds
    off prod). CPO-ACCEPTED as residual for this PR (2026-07-08, this conversation); deferred to #667 (shared prod
    concurrency group; pages needs a job-level group so its Pages deploy isn't serialised behind dbt runs).

done_when:
  - generate_schema_name prefixes the custom-schema branch by target.name; `prod` bare, all other targets prefixed.
  - ci-data-build.yml: PR = `--target ci` + `--defer --favor-state` against a prod-compiled baseline; push =
    `--target prod`; the `dbt seed` AND singular-DQ steps are split PR-vs-push; the data-build job carries a
    `concurrency:` guard serialising writes to the shared `ci_*` dataset.
  - dbt-scheduled.yml + pages-match-preview.yml pin `--target prod` (canonical bare datasets).
  - profiles.example.yml documents dev/ci/prod outputs + the "prod is the only bare target" rule.
  - operations_guide.md + layering.md carry a short environments/targets note.
  - validate-local gates green; analytics-engineer-reviewer + cto-reviewer PASS; review.md diff_sha256 binds; CPO merges.

amendments:
  - 2026-07-08 (CPO-approved this conversation): broadened protected_override + the ci-data-build.yml edit scope to
    add (a) the per-event `dbt seed` target split and (b) a job-level `concurrency:` guard — both remediation of
    blinded-review FAILs (analytics-engineer: the push-path `dbt seed` wrote to `ci_analytics` while the prod build
    reads seeds from `dbt_analytics`, so post-merge prod builds would read stale seeds / fail; cto: concurrent-PR
    MERGE serialize-access race on the shared `ci_*` dataset). No governance-behaviour change to the guards.
