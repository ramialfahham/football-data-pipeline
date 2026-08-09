# Task contract — #39 Stage 1: move the nightly out of CI onto Cloud Run

objective: >
  Package the nightly pipeline as a container and run it on Cloud Run Jobs, triggered by Cloud
  Scheduler at 04:00 UTC, so the production data plane stops living inside GitLab CI. A CI-side
  event has taken the product's data offline twice in four days — the migration silently dropped
  the cron (6 days stale, unnoticed), then the namespace hit `ci_quota_exceeded`. Neither cause
  had anything to do with data.

  Stage 1 is the split ONLY. No Python changes: the `data:nightly` shell logic is ported 1:1 into
  a container entrypoint. `.gitlab-ci.yml` is NOT edited — the GitLab schedule is paused instead,
  keeping the old path as a manual fallback until the new one has proven itself.
refs: GitLab #39 (Stage 1 of 3); #33 items 7, 14, 16

scope_paths:
  - Dockerfile
  - .dockerignore
  - .gitattributes
  - deploy/nightly/entrypoint.sh
  - deploy/nightly/profiles.yml
  - deploy/nightly/README.md
  - tests/test_nightly_entrypoint_parity.py
  - .claude/task/contract.md
  - .claude/task/escalations.log
  - .claude/task/review.md
  - .claude/task/review_input.patch

# Not gate-required — no path here is on the structural surface (`ingestion/**`,
# `dbt_project/models/**`, `scripts/export_*.py`, `site*/`, protected paths). Included
# anyway: this creates a SECOND production execution path for the whole pipeline, which is
# a wider blast radius than most model edits, and a reviewer should not have to take that
# on trust.
impact_map: >
  what this changes: nothing in the pipeline's CODE. It adds a second way to INVOKE the
    existing entrypoint `python -m ingestion.api_football.main` followed by the same
    `dbt deps / seed / build --target prod`. Verified against `.gitlab-ci.yml` `data:nightly`
    (lines 667-711): the ported step list and order are identical, including the `new_data`
    gate and both contract checks.

  writers: the container runs the SAME ingestion package that writes every RAW_APIF_* table,
    and the same `dbt build --target prod` that writes `dbt_analytics`. No new writer is
    introduced and no write path is altered.

  downstream: unchanged. The nightly's outputs are the raw tables and the prod warehouse; both
    are produced by the identical commands. `dbt ls` lineage is untouched because no model,
    macro or seed is edited in this task.

  concurrency: the existing BigQuery ingest lock (`ingestion/api_football/ingestion_lock.py`,
    `RAW_APIF_INGEST_LOCK`) is what prevents a Cloud Run run and any GitLab run from colliding
    — it is dataset-level, not CI-level, so it already spans both platforms. This is why the
    GitLab job can remain in place as a fallback rather than having to be deleted first.
    `--max-retries 0` is set deliberately: the lock holds a lease, so an immediate retry would
    be refused and only add noise.

  credentials: the job runs AS `github-actions-dbt@football-data-pipeline-gcp.iam.gserviceaccount.com`,
    the service account that already holds the BigQuery roles used by CI. `method: oauth` +
    `google.auth.default()` resolves it natively inside Cloud Run — no WIF exchange and no key
    file. TWO new IAM grants, both in `deploy/nightly/README.md`, both enumerated here because
    an earlier draft of this paragraph claimed there was only one and `cto-reviewer` and
    `platform-reviewer` each caught it independently (round 1):
      1. `roles/secretmanager.secretAccessor` on the secret `api-football-key` — lets the job
         read the API key at runtime instead of baking it into an image layer.
      2. `roles/run.invoker` on the JOB `fdp-nightly` — lets Cloud Scheduler start it.
    Grant 2 is RESOURCE-scoped, not project-scoped. The project-scoped form would let this
    identity invoke every Cloud Run service and job in the project, present and future, and
    `github-actions-dbt` is not single-purpose — it is the same account CI impersonates to write
    the prod warehouse. Widening a shared production identity is not something this task needs
    and is not something it does.

  deploy_order: nothing breaks at any point. The container is additive; until the Cloud Run job
    is deployed AND the GitLab schedule paused, behaviour is exactly as today. The two can
    never both fire because pausing the schedule precedes the first scheduled Cloud Run run,
    and the ingest lock backstops it regardless.

  blast_radius: no mart, model or number changes. The risk is operational, not analytical: if
    the container is wrong, the nightly fails and data goes stale — the failure mode that
    already exists today and that Stage 2 (#33 item 16 freshness alerting) is what actually
    closes. Stage 1 does not close it and does not claim to.

decisions_taken: >
  The CPO approved the architecture and this stage explicitly: "start with #39", then "plan
  stage 1", then approval of the written plan. Region `europe-west1` and Secret Manager for the
  API key were both chosen by the CPO when asked.

  Framing ruling that constrains this task: "the nightly run is the minimum of updates we need
  so data doesn't become stale." Cadence is therefore NOT available as a cost lever, which is
  what rules out the cheaper options (reduce frequency, wait for the quota reset) and forces the
  hosting change.

  CPO also ruled out, in this conversation: buying GitLab compute minutes, and applying to the
  GitLab for Open Source programme.

  # THRESHOLD DECLARATIONS
  NEW MECHANISM — YES. Cloud Run Jobs, Cloud Scheduler and a container image are all new to this
  repo; nothing here runs on them today. Declared rather than smuggled: this is the CTO-class
  threshold and no routing row covers `Dockerfile` or `deploy/**`, so `cto-reviewer` is spawned
  for this task even though `.claude/review_routing.json` does not require it.

  RECURRING COST — YES. ~1 vCPU / 2 GiB for ~110 min/day ≈ **$1.70/month** on the existing GCP
  bill, falling to ~$0.35 once #33 item 14 removes the redundant re-fetching. Cloud Scheduler is
  free at this volume. Secret Manager ~$0.06/month. Against this it returns the whole 400
  GitLab minutes/month to CI across all three of the owner's projects, and today the nightly
  cannot run at all.

  NO new Python dependency is added — `requirements.txt` is unchanged; the image installs
  exactly what CI installs.

decisions_reserved:
  - When `data:nightly` is deleted from `.gitlab-ci.yml`. It is a protected path needing its own
    governance task with `protected_override`, and it should not happen until the Cloud Run job
    has run successfully at least once. Not decided here.
  - Whether ingest and dbt stay one job or split into two chained jobs (#39 open question).
  - Stage 2 (freshness alerting, #33 item 16) and Stage 3 (CI builds and pushes the image) are
    separate tasks. Stage 1 deliberately leaves the staleness blind spot open.
  - Per-competition task sharding — later, and constrained by the provider's per-minute rate
    limit and the global daily quota.

done_when:
  - `pytest tests/ -q` exits 0 (baseline on main is 720 passed, 1 skipped).
  - `ruff --config .ruff-ci.toml ingestion/ tests/` exits 0.
  - The parity test is verified by BREAKING its subject: remove a step from the entrypoint and
    confirm the test goes red, then restore.
  - `deploy/nightly/entrypoint.sh` is confirmed to be a faithful port by diffing its step list
    against `.gitlab-ci.yml` `data:nightly` by hand, not by assertion.
  - No `gcloud` resource is created and no ingest is run from this branch. Deployment is blocked
    on the CPO enabling Secret Manager and creating the API-key secret, and is a separate,
    deliberate step with the log watched.

amendments:
  - 2026-08-09: + `.gitattributes` — authority: **CPO, asked and answered in-thread: "yes, add
    .gitattributes"**. An earlier draft of this entry cited builder judgement instead and
    `scope-auditor` FAILed it in round 1, correctly: working_agreement §2 requires an amendment
    to record the CPO's authority, and §219-221 makes extending scope without it drift by
    definition. Recording that no authority was sought is not the same as having it.
    The alternative offered to the CPO was stripping CRs inside the Dockerfile, which is already
    in scope; it was declined as symptom-treatment that leaves the repo still corrupting shell
    scripts for anyone who clones it. Content: `*.sh` and `Dockerfile` pinned to `eol=lf`.
    WHY IT IS NOT OPTIONAL: `core.autocrlf=true` on this machine and the repo has no
    `.gitattributes`, so `deploy/nightly/entrypoint.sh` is LF only because it was just
    written — any fresh clone or `git checkout` converts it to CRLF. `gcloud run jobs deploy
    --source .` uploads the WORKING TREE, so the image would ship a script whose shebang is
    `#!/usr/bin/env bash\r`, and the container would fail with "no such file or directory"
    at 04:00 in production. It fails nowhere earlier: tests pass, the build succeeds, and the
    parity test reads the file as text.
    Deliberately narrow — two patterns, both consumed only by Linux tooling. A repo-wide
    normalisation would rewrite unrelated files and is not in scope.
