# Task contract — MR pipelines test the merged result

objective: >
  Issue 314, How step 1. MR pipelines test the branch merged with the latest target branch.
  Scratch datasets are named per main version and listed for deletion by a dry-run script. The
  MR data build gets a resource group per merge request and waits while a prod build runs. The
  full design sweep on main coalesces. Together these stop the four causes of the
  15 Nov 2026 red pipelines that this MR covers.

refs: >
  Issue 314 (approved in chat, 15 Nov 2026), How step 1.

scope_paths:
  - .gitlab-ci.yml
  - scripts/list_mr_scratch.py
  - scripts/check_sweep_superseded.py
  - tests/test_merged_result_ci.py
  - tests/test_list_mr_scratch.py
  - tests/test_check_sweep_superseded.py
  - tests/test_ci_data_job_invariants.py
  - tests/test_sentence_length_in_docs.py
  - dbt_project/docs/layering.md
  - docs/operations_guide.md
  - .claude/task/314-merged-result-ci/contract.md
  - .claude/task/314-merged-result-ci/review.md
  - .claude/task/314-merged-result-ci/review_input.patch

protected_override: >
  .gitlab-ci.yml edit approved in chat, 15 Nov 2026, as issue 314; the MR head declares the
  locked file.

impact_map: >
  writers: no model, seed or raw table changes. .gitlab-ci.yml changes four jobs and adds one:
  test:python, build:site-v2, validate:ui (merged result; a resource group per branch, and on a
  push to main a first step that stops a sweep a newer push covers), data:build:mr (merged
  result, per-MR resource group, scratch dataset name, seed diff base, the nightly wait), and the
  new data:wait-prod-build gate in prod-warehouse-write, which data:build:mr needs.
  data:build:main, data:nightly, the deploy jobs and validate:governance keep their scripts; the
  one shared piece they read is the .dbt_profile anchor, whose prod output is unchanged and
  whose non-MR scratch name stays ci_mrshared.
  downstream: readers of DBT_CI_TARGET and of the ci_mr prefix, from
  `grep -rn "DBT_CI_TARGET\|ci_mr" scripts tests dbt_project/macros docs .claude/hooks`:
  tests/test_ci_data_job_invariants.py (derivation and dataset pins),
  dbt_project/docs/layering.md lines 29 and 34, docs/operations_guide.md lines 244-245. No script
  or macro reads either; macros/generate_schema_name.sql prefixes with target.name and is
  unchanged. wait_for_nightly.py is unchanged; data:build:main calls it and data:build:mr now
  calls it too. The gate job joins prod-warehouse-write with data:build:main and data:nightly;
  it checks out nothing and runs one echo, so it holds the group for seconds.
  check_sweep_superseded.py reads validate:ui's own main `changes:` rule from .gitlab-ci.yml,
  and nothing else imports it; on any error it exits non-zero and the full sweep runs.
  layer_rules: not applicable, no model changes; check_layer_contract.py is unaffected.
  deploy_order: takes effect on the next pipeline after merge. Existing ci_mr<IID> datasets are
  no longer written; list_mr_scratch.py lists them. The resource group for main's validate:ui is
  created by its first main pipeline; its newest_first mode is then set by one API call the CPO
  runs (GitLab API write).
  blast_radius: every MR pipeline. A merge conflict with the target turns test:python,
  build:site-v2, validate:ui and data:build:mr red, which matches what the MR could not merge.
  validate:governance still tests the branch, so the review hash is unchanged. Two MRs' data
  builds can now run at once on the one runner's two slots.

approved_design:
  - none: no page output changes

decisions_taken: >
  The five items of issue 314 How step 1, approved in chat, 15 Nov 2026. The wait on a prod
  build is the no-op gate job the issue names. An older main sweep stops itself when a newer
  push touching validate:ui's main `changes:` list has its own sweep; the coordinating session
  chose this route, because newest_first alone only reorders the waiting sweeps.
  dbt_project/docs/layering.md loses one long sentence, so its pin in
  tests/test_sentence_length_in_docs.py moves down by one. validate:ui also tests
  the merged result, because it measures build:site-v2's merged dist against the branch's own
  baselines and tests, and the two must be one tree. NEW MECHANISM declared: the merged-result
  step, list_mr_scratch.py, the gate job, check_sweep_superseded.py, and the per-MR and
  main-sweep resource groups. RECURRING COST declared: a scratch dataset set per main version accumulates until the
  CPO deletes from the list_mr_scratch.py output, which issue 314 names as the cleanup route;
  nothing here deletes or expires a dataset.

decisions_reserved:
  - none: the main sweep group's newest_first mode is a GitLab API write the CPO's coordinating
    session runs after the first main pipeline creates the group; nothing here sets it.

done_when:
  - python -m pytest tests/ -q is green inside python:3.11, as test:python runs it.
  - dbt parse passes; the validate:governance scripts pass.
  - The offline gates in FAST_GATES pass.
  - The MR pipeline is green and its test:python, build:site-v2 and data:build:mr logs show the
    merged-result step.

amendments:
  - 2026-11-15: + tests/test_sentence_length_in_docs.py, - scripts/wait_for_nightly.py,
    - tests/test_wait_for_nightly.py — authority: issue 314 (approved in chat, 15 Nov 2026), whose
    wait item names the gate job; content: the pin moves down by one, and the wait script is
    called unchanged.
