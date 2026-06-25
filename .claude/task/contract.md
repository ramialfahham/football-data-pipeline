# Task contract — Slim CI: PR builds only changed models (dbt state:modified+)

> Governance G2/G3 contract. Written on a clean tree BEFORE any code edit.
> See docs/working_agreement.md §2 (contract), §10 (decision rights), §11 (escalation).

objective: >
  Cut BigQuery build cost by making `ci-data-build` PULL-REQUEST runs build ONLY the
  models a PR changed plus their downstream children + tests (dbt `state:modified+`),
  instead of rebuilding the whole warehouse (base->marts) on every push. Measured driver
  (INFORMATION_SCHEMA.JOBS_BY_PROJECT, 14d): the full-refresh dims dim_player (~2.5 GB/run),
  dim_player_team_season_mapping (~1.9), dim_team (~0.7) = ~750 GB alone, rebuilt on every
  PR even when untouched. After this, those (and the transfers chain) rebuild only when
  their own lineage changes. The 04:00 scheduled prod refresh (dbt-scheduled.yml) is
  UNCHANGED -- it ingests fresh data and must rebuild everything.
refs: #547 (cost optimization); cost diagnosis 2026-06-25.

scope_paths:
  - .github/workflows/ci-data-build.yml

protected_override: >
  CPO approved in conversation 2026-06-25: "A with Option 2" -- slim CI via dbt
  `state:modified+` on ci-data-build.yml, Option-2 baseline (compile `main` at PR time).
  `.github/workflows/**` is a PROTECTED prefix (task_contract_gate.PROTECTED_PREFIXES);
  this task is its dedicated, CPO-approved governance change. Routes to cto-reviewer on the
  opus floor + scope-auditor (always).

decisions_taken: >
  - SCOPE = pull_request builds only. main-push and workflow_dispatch keep the FULL
    staging+downstream build (prod must stay complete and serve as the always-compilable
    baseline). dbt-scheduled.yml (04:00 prod) is untouched.
  - BASELINE = Option 2 (compile `main` at PR time via a git worktree). Chosen over
    Option 3 (GCS/artifact-stored manifest): no bucket/artifact plumbing, no cold-start,
    deterministic; the only cost is ~30-60s compile wall-time, which scans NO BigQuery
    bytes (compile builds the manifest, it does not execute models).
  - CORRECTNESS on the shared warehouse: state:modified+ does not rebuild unchanged
    upstreams; their ref()s resolve to tables already materialized in the shared datasets
    (CI writes to the same prod datasets -- generate_schema_name returns the bare schema
    regardless of target), so NO --defer is needed. A typical PR rebuilds FEWER models into
    prod than today, never more -- A reduces prod churn.
  - DATA QUALITY stays full: the singular-test step still runs the WHOLE singular suite on
    every PR (DQ is non-negotiable, CLAUDE.md). Slimming applies to model BUILDS only.
  - Freshness tests stay excluded on PR builds (tag:freshness_check) -- preserved via CLI
    `--exclude` (honoured with `--select`; only a named `--selector` drops `--exclude`).

# Informational only -- .github/workflows is NOT the gate's structural surface
# (ingestion / dbt_project/models / export / site). No impact_map key is required; the
# blast radius is recorded here for the cto-reviewer.
notes_blast_radius: >
  No model/seed/macro/test SQL changes -- model outputs are byte-identical. This is a CI
  orchestration change. The only behavioural delta: WHICH models a given PR rebuilds.
  Validation coverage for the PR's own changes is preserved (state:modified+ includes ALL
  descendants + their tests); the full singular DQ suite still runs. No migration; the
  first model-touching PR after merge exercises the slim path (this PR changes no models,
  so its own slim build is a no-op pass -- expected).

decisions_reserved:
  - CI writing into the PROD datasets at all (no dev/prod isolation; generate_schema_name
    ignores target) is a separate, larger decision -- NOT in this task; flagged, do not fold in.
  - Slimming the singular DQ suite to state:modified+ if test scan-cost later proves
    material -- deferred; revisit only with evidence (DQ stays full for now).
  - Migrating to Option 3 (stored manifest) if compile wall-time becomes a bottleneck --
    deferred; revisit only with evidence.

done_when:
  - ci-data-build.yml PR path runs `dbt build --select state:modified+ --exclude
    tag:freshness_check --state <main-manifest>`; the baseline is compiled from origin/main
    via a git worktree at PR time; main-push + workflow_dispatch keep `--selector staging`
    then `--selector downstream`; dbt-scheduled.yml is untouched.
  - Workflow is internally consistent: baseline-compile produces the `--state` dir; deps/
    seed/auth ordering preserved; freshness exclusion preserved on both paths; bootstrap-
    ingest steps and the terminal `gate` job unchanged; YAML parses.
  - `python .claude/hooks/git_discipline.py --staged-hash` == review.md diff_sha256;
    scope-auditor + cto-reviewer PASS (each >=2 named risks); no FAIL, no open ESCALATE.

amendments: (none)
