# Task contract — nightly site export, build and deploy from live data

objective: >
  Issue 156: every night, after the warehouse nightly (`fdp-nightly`, 04:00 UTC), export the entities the
  built pages read, build the site at the deploy job's heap, and deploy it to Firebase only when
  `audit-seo` and `check-built-pages` are green, with no manual step. One Cloud Run job `fdp-site`,
  started by a third Cloud Scheduler entry, runs `scripts/nightly_site_deploy.py`. The committed sample
  under `site_v2/src/data/` stays the MR build's input and its README already says so; production no
  longer shows the sample.

refs: >
  Issue 156 (How steps 1 to 4), gate issue 290 (its list names the nightly live-data deploy). Issue 155 is
  closed and fixed on main, so step 2 of the How has nothing left to fix. The disabled GitLab schedule
  4379625 is not touched.

scope_paths:
  - scripts/export_site_data.py
  - scripts/nightly_site_deploy.py
  - tests/test_deploy_entities.py
  - tests/test_nightly_site_deploy.py
  - tests/test_governance_hooks.py
  - deploy/site/**
  - deploy/nightly/README.md
  - deploy/nightly/alert-policy.json
  - .gitlab-ci.yml
  - .claude/task/156-nightly-site-export-deploy/contract.md
  - .claude/task/156-nightly-site-export-deploy/review.md
  - .claude/task/156-nightly-site-export-deploy/review_input.patch
  - .claude/task/156-nightly-site-export-deploy/measurement.md

protected_override: >
  `.gitlab-ci.yml` is edited to add the image build and deploy pair for `fdp-site` and to point
  `deploy:export` at the shared entity list. Gate issue 290 lists the nightly live-data deploy; its list was
  approved in chat, 2026-11-11. The one full local export that measures the cost was approved in chat,
  2026-11-21. The MR head declares the locked file and the merge is the approval.

impact_map: >
  writers: `scripts/export_site_data.py` is the only writer of `site_v2/export_data` and of the nightly
  job's export folder. No dbt model, raw table, seed or mart is added or changed.
  downstream: readers of `ENTITY_TYPES` and of the script (`grep -rln "export_site_data\|ENTITY_TYPES"
  --include=*.py --include=*.yml`): `.gitlab-ci.yml` (`deploy:export`), `tests/test_catalogue_order.py`
  (imports the module), `scripts/check_layer_contract.py` (reads the file path), and
  `site_v2/scripts/check-metric-labels.test.mjs` (reads the source text for named blocks); several other
  tests import the module and are unaffected because the change is additive. The new constants
  `DEPLOY_ENTITIES` and `ENTITY_OUTPUTS` and the function `parse_entities` sit beside `ENTITY_TYPES`;
  `ENTITY_TYPES` and the default of `--entities` do not change. No dbt lineage: no model is touched.
  layer_rules: not applicable, no model change; `check_layer_contract.py` still passes (it only reads the
  script path). Guard invariants: no BigQuery write (the export SELECTs marts and seeds only), the manual
  deploy job stays reachable only by web dispatch, and the new image jobs run only on a push to main and
  fail closed.
  deploy_order: the image jobs fire on a push to main that changes what the image carries (the paths in
  `.site_image_paths`). `gcloud run jobs update fdp-site` needs the job, so after the first merge
  `deploy:site-image` is red until the runbook's create step is done; it is then re-run. The nightly
  (`fdp-nightly`, 04:00) is untouched. The scheduler entry is created last, after the first run of the
  merged job succeeded, and never before this MR merges.
  blast_radius: a nightly deploy replaces the live Firebase site. Guards that stop it: the warehouse nightly
  must have finished today; the export's counts must hold at 90 percent or more of the live site's, and a
  live site without the counts file refuses the deploy unless the run is flagged as the first; both build
  gates must be green. The site stays `noindex` and `INDEXABLE` stays false.

approved_design:
  - none: no page output changes

depends_on:
  - none: no open merge request exists to depend on; main already holds issue 155's fix

shared_files:
  - none: no design baseline, component registry, font coverage or chart screenshot file changes

decisions_taken: >
  The builder's recommendation for where the schedule lives, ruled by the coordinating session: a Cloud Run
  job `fdp-site` and a third Cloud Scheduler entry after `fdp-nightly`. A GitLab pipeline schedule is
  not used: a 20 to 113 minute build of about 16 GB of files would hold one of the runner's two slots
  and its disk. Because it is a new mechanism with recurring spend, the choice is also in
  decisions_reserved, so the MR head puts it to the CPO and the merge is the answer.
  NEW MECHANISM, declared for cto-reviewer: one Cloud Run job, one Cloud Scheduler entry, one image
  (`deploy/site/Dockerfile`) built by a kaniko job pair that mirrors `build:nightly-image` and
  `deploy:nightly-image`, one alert policy, two job-scoped role grants on `fdp-site` (run.developer for
  the CI repoint, run.invoker for the scheduler), and one Artifact Registry cleanup policy. It reuses the
  pipeline service account; its warehouse guard repeats the execution-list call of
  `scripts/wait_for_nightly.py` with different semantics (the newest execution, created today, succeeded).
  RECURRING COST, declared for cto-reviewer and the CPO:
  - Cloud Run: about 0.6 USD per night for 8 vCPU and 32 GiB for about 50 minutes, replaced by the measured
    minutes. The filesystem of a Cloud Run job is memory; the export, `dist` and the build heap take about
    25 GB at the peak.
  - BigQuery: about 3.4 GiB per export, about 0.02 USD a run, about 0.6 USD a month.
  - Firebase storage beyond 10 GB at 0.026 USD per GB-month for the retained releases, bounded by
    `maxVersions`.
  - Artifact Registry: one image of about 1 GB per push to main that changes what the image carries, at
    0.10 USD per GB-month, bounded by a cleanup policy that keeps the latest five `fdp-site` versions.
  - Runner time: each kaniko build holds a runner slot for up to 30 minutes on a push to main that changes
    what the image carries.
  The measured figure goes at the top of the MR head. It is measured before the merge, on this machine, from
  one full local run of the same image: the export's billed bytes from INFORMATION_SCHEMA, the build minutes
  and peak memory, and the size of `dist`, which also bounds the Firebase upload. Deploying a branch to the
  live site to measure it is not done. The first run of the merged job confirms the figure, and the schedule
  entry is created only after that run succeeded. The CPO's merge with the measured number in the head is the
  approval, and no schedule is enabled before that merge.
  Firebase release retention is capped at a few versions through the Hosting API `maxVersions` setting,
  applied once by the runbook (it is a site setting, not a file in the repo).
  The count guard: the export manifest's counts are compared with a small file the previous deploy published
  at `/export-manifest.json` on the live site (counts and the export's source counts, nothing else; no
  checksums, no row data). The deploy is refused when team, fixture, competition, player or player_peers
  falls under 90 percent of that file's value (a key with fewer than 20 rows before is ignored, and a
  missing key counts as a fall). Unplayed and match-day counts are not compared: they fall legitimately
  after a round is played. A 404 on the file refuses the deploy unless the execution carries
  `ALLOW_FIRST_DEPLOY=1`, and the run then logs that the floor was skipped. That is the first deploy, and
  the first deploy after a manual fallback deploy, which publishes no counts file. Any other fetch error
  refuses, so a bad night is never mistaken for a first one.
  The warehouse guard: the newest `fdp-nightly` execution must have been created today (UTC) and have
  completed successfully; one still running is waited for up to 45 minutes; anything else refuses the deploy.
  One entity list: `DEPLOY_ENTITIES` in `scripts/export_site_data.py` (the entities every page reads;
  `nav`, `leaderboards` and `glossary` are not read by any page), selected by `--entities deploy`, read by
  both `deploy:export` and the nightly script. `tests/test_deploy_entities.py` pins it to the data files the
  committed sample holds, which is the set of files the pages read.
  The image build uses the Dockerfile's own ignore file, copied over the checkout's `.dockerignore` before
  kaniko runs: the shared `.dockerignore` excludes `site_v2/`, which the nightly image must not carry.
  `deploy:site-image` fails on every error, including a missing job.
  Known and not closed here: the built pages load club crests and, until the photo rule is built, player
  photos from the data provider's host. Both are already on main and no build gate checks the origin.

decisions_reserved:
  - whether the CPO accepts the Cloud Run job plus Cloud Scheduler mechanism and its measured recurring cost:
    put on the MR head with the number and the rejected alternative, a GitLab pipeline schedule
  - whether the live site may carry a public `/export-manifest.json` of row counts: if not, the count
    baseline moves to a Cloud Storage object, which is a new bucket and a new grant
  - the Firebase `maxVersions` value and the Artifact Registry cleanup policy (keep five), if different
    values are wanted
  - the creation of the Cloud Run job, the role grants, the scheduler entry, the cleanup policy and the first
    run, which are runbook steps for someone with `gcloud` rights on the project; the first run deploys live
    data to the `.web.app` site

done_when:
  - python -m pytest tests/ -q is green, including tests/test_deploy_entities.py and tests/test_nightly_site_deploy.py
  - the offline gates in FAST_GATES pass
  - python scripts/ci_local.py --mr is green
  - one full local run of the same steps is measured (BigQuery billed bytes, build minutes, peak memory, size of
    `dist`, gate result) and the recurring cost is at the top of the MR head
  - the MR pipeline is green

amendments: (none)
