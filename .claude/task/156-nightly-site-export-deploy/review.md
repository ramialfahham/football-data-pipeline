# Review — claude/156-nightly-site-export-deploy

diff_sha256: 5083294c6dde6e30d46844eeaedaadae8621e61703c26501f1b3b4e0da61af29

rounds: 2

## scope-auditor
VERDICT: PASS
risks_checked:
- Scope: every file of the cumulative patch, the new `deploy/site/cleanup-policy.json` included, matches a `scope_paths` entry; `amendments` is `(none)`. `site_v2/src/data/README.md` is not in the patch.
- `protected_override` for `.gitlab-ci.yml` names the issue 290 gate list (approved in chat, 2026-11-11) and the local measurement export (approved in chat, 2026-11-21), with the MR head declaring the locked file. Both approvals carry a date and a place and quote no words.
- Decision rights: the Cloud Run plus Cloud Scheduler mechanism is a new mechanism with recurring cost, declared in `decisions_taken` and also in `decisions_reserved` with the rejected alternative. No scheduler entry, job, grant, cleanup policy or `maxVersions` is made by the diff; all stay runbook steps.
- Thresholds: the new mechanism, the Cloud Run, BigQuery, Firebase, Artifact Registry and runner costs and the public `/export-manifest.json` are each declared with their authority path. No page output changes (`approved_design: none`).

## cto-reviewer
VERDICT: PASS
risks_checked:
- Artifact Registry storage that grew without limit: closed by `deploy/site/cleanup-policy.json` (keep five `fdp-site` versions) with a runbook warning that setting policies replaces the repository's; the cost and runner time are declared.
- Count floor after a manual fallback deploy: closed, a missing counts file refuses unless `ALLOW_FIRST_DEPLOY=1` is set on that execution, and any other fetch error refuses.
- `deploy:site-image` is a bare `gcloud run jobs update`, failing on every error like `deploy:nightly-image`; contract and runbook agree on the red first run and the re-run.
- Cost approval order: the cost is measured on a local run of the same image before the merge, the first run of the merged job confirms it, and the schedule entry comes after that run.
- Authority: the protected override names dated approvals and the mechanism is reserved for the CPO. The two job-scoped role grants, the cleanup policy and the new image jobs are declared; no new dependency or credential.

## platform-reviewer
VERDICT: PASS
risks_checked:
- The CI repoint step fails closed, and the missing permission has a job-scoped `roles/run.developer` grant in the runbook.
- `.site_image_paths` covers the seeds, the core and mart models, the registry, the component list and `site_v2/`; a sweep of the repo-root reads under `site_v2/` found nothing else, and a governance test names each path.
- Count floor, warehouse guard, step failures and the image repoint all fail closed; `deploy()` is tested for step order, a failed export or build stopping before the Firebase deploy, a count fall stopping before the build, and the counts file reaching `dist/`.
- The export is moved into the build folder, not copied, so the memory-backed disk holds it once; the 25 GB peak fits the 32 GiB job.
- Provider-hosted images on built pages (`Crest.astro`, `PlayerRow.astro`) are open and recorded in the contract as known and not closed here; the coordinating session runs it as its own stream.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Alert policy text no longer carries a backticked job name, so the parity test finds no unknown `fdp` token; the runbook's monitoring section states four policies and lists the new row.
- `DEPLOY_ENTITIES` equals the eleven entities the old `deploy:export` list named, `ENTITY_TYPES` and the `--entities` default are unchanged, and `ENTITY_OUTPUTS` matches what `export_all` writes.
- No dbt model, seed or mart changes; the count floor and nightly-state logic are deploy guards on file counts, not metrics; the entity-set test pins the export to the files the committed sample holds.

## escalations
(none)
