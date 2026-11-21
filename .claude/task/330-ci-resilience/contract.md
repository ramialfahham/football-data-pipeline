# Task contract — the MR data build rebuilds the prod models that are stale, and skips MRs with no dbt-relevant change

objective: >
  Issue 330. data:build:mr builds every prod model that is older than one of its parent tables,
  with its descendants, into the merge request's own datasets, so its deferred reads only ever
  meet consistent prod tables. It no longer triggers on paths that cannot change what dbt builds
  or tests in it. One reviewer-checklist line is added.

refs: >
  Issue 330 (approved in chat, 20 Nov 2026), reworked as approved in chat the same day.

scope_paths:
  - .gitlab-ci.yml
  - scripts/stale_prod_nodes.py
  - tests/test_stale_prod_nodes.py
  - tests/test_ci_data_job_invariants.py
  - dbt_project/docs/layering.md
  - .claude/agents/analytics-engineer-reviewer.md
  - .claude/task/330-ci-resilience/contract.md
  - .claude/task/330-ci-resilience/review.md
  - .claude/task/330-ci-resilience/review_input.patch

protected_override: >
  .gitlab-ci.yml and .claude/agents/analytics-engineer-reviewer.md edits approved in chat,
  20 Nov 2026, as issue 330; the MR head declares the locked files. The reviewer line is the text
  the CPO approved in chat on 20 Nov 2026.

impact_map: >
  writers: no model, seed or raw table changes. .gitlab-ci.yml changes one anchor, .data_paths_mr,
  one comment above .data_paths_image, and one job, data:build:mr, which gains one script line and
  a selection on its `dbt build`. data:build:main, data:nightly, the deploy jobs and
  validate:governance keep their scripts; .data_paths_prod is untouched. dbt_project/docs/layering.md
  changes one paragraph that says what a merge request is tested on.
  downstream: readers of .data_paths_mr, from `grep -n "data_paths_mr" .gitlab-ci.yml` and
  `grep -rn "data_paths_mr" tests scripts docs`: data:wait-prod-build and data:build:mr in
  .gitlab-ci.yml, tests/test_ci_data_job_invariants.py and tests/test_merged_result_ci.py (which
  keeps the two rules equal). scripts/stale_prod_nodes.py is new and is called by no other job.
  A dbt file reads none of the dropped paths: `grep -rn "scripts/\|ingestion/" dbt_project` finds
  comments and descriptions only.
  layer_rules: not applicable, no model changes.
  deploy_order: takes effect on the next MR pipeline after merge. The new step reads the manifest
  that data:build:mr already compiles from the target commit with --target prod, and BigQuery
  metadata of the prod datasets with the credentials the job already holds.
  blast_radius: every MR pipeline that triggers data:build:mr. While prod is whole the new step
  finds nothing and the build is unchanged: against the live prod of 20 Nov 2026 it finds 0 stale
  models of 138. While prod is partly built, the build also runs the stale models and their
  descendants and their tests; a test of those that fails on the rebuilt data is the MR's
  to fix, as a prod test it does not touch is not selected. MRs touching only scripts/check_*.py,
  scripts/data_trust_*.py or ingestion/ get no data build. If the metadata read fails the job
  fails before any dbt build.

approved_design:
  - none: no page output changes

depends_on:
  - none: the change reads .gitlab-ci.yml as it is on main; !492, !493 and !491 touch no CI file

shared_files:
  - none: no design baseline, component registry, font coverage or chart screenshot changes

decisions_taken: >
  The three items of issue 330, approved in chat, 20 Nov 2026, with the route for item 1 approved
  in chat the same day: no stop and no override. A prod model is stale when one of its parent
  tables was modified after it, which is exactly where a deferred read would meet a child older
  than its inputs; it covers a nightly's skips, a data:build:main's, and a build interrupted halfway.
  Seeds and sources count as fresh, because the build does not rebuild them as models; a view or an
  ephemeral model is passed through to its table parents. The source is the prod manifest that
  data:build:mr already compiles into /tmp/main-state, and the last-modified times of the prod
  datasets in BigQuery's __TABLES__ metadata, which a dry run measured at 0 bytes. The
  last prod run's run_results.json is not used: data:build:main publishes only the manifest, the
  catalog and the docs page, and its dbt seed, two builds and test each rewrite that file, and the
  nightly persists nothing. NEW MECHANISM declared: scripts/stale_prod_nodes.py.
  RECURRING COST declared: on a day prod is partly built, each MR data build also builds the stale
  models and their descendants into its own datasets, about the build size of the models that run
  skipped and at most one full prod build per MR pipeline; the nightly's measured cost in CLAUDE.md
  is about 129 GB a day for the nightly and the freshness sentinel together, which is the scale.
  On a whole prod it is nothing. The trigger narrowing lowers cost: an MR changing only the dropped
  paths no longer starts a BigQuery build. dbt_project/docs/layering.md states what a merge
  request is tested on and now names the stale models, a one-paragraph edit the CPO's merge approves.

decisions_reserved:
  - none: nothing else is open.

done_when:
  - python -m pytest tests/ -q is green.
  - python scripts/ci_local.py --mr passes.
  - scripts/stale_prod_nodes.py run against live prod returns no stale model, and a test with the
    timestamps of a partly built prod returns the skipped models and their descendants.
  - The MR pipeline is green and python scripts/merge_ready.py <iid> says ready.

amendments: (none)
