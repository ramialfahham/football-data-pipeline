# Task contract — merge request build: rebuild a changed seed even when it is over 1 MB

objective: >
  data:build:mr rebuilds every seed the merge request changed, and every model that reads it,
  whatever the seed's size; a merge request that changes no seed builds what it builds today; a
  build that cannot tell which seeds changed fails. A test in tests/test_ci_data_job_invariants.py
  fails when either half is removed.

refs: >
  #214 (https://gitlab.com/rami.al-fahham/football-data-pipeline/-/work_items/214). Found on the
  MLS line-up batch, !310, whose data:build:mr selected nothing because dbt cannot fingerprint a
  seed over 1 MB.

scope_paths:
  - .gitlab-ci.yml
  - tests/test_ci_data_job_invariants.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md

impact_map: >
  writers: data:build:mr only, in its own ci_mr<IID>_* datasets; data:build:main, fdp-nightly and
  every other job are unchanged.
  downstream: a merge request that changes a seed rebuilds that seed's readers in its own datasets,
  so its singular tests read the branch's tables instead of prod's.
  layer_rules: none; no dbt file changes.
  deploy_order: none; the change applies to the next merge request pipeline.
  blast_radius: merge request pipelines that change a seed: more models built in their own
  datasets. A merge request without a seed change selects exactly what it selects today.

protected_override: >
  .gitlab-ci.yml, job data:build:mr only: the changed-seed selection on its dbt build line. The
  plan naming this edit approved in chat, 2026-10-12.

decisions_taken: >
  The CI fix as a separate merge request, merged before !310: approved in chat, 2026-10-12.

  THRESHOLD DECLARATIONS: NEW MECHANISM: none; one more selector on the existing state:modified+
  build. RECURRING COST: none on any schedule; a merge request that changes the line-up seed
  rebuilds 14 models, estimated at 4-5 GB of BigQuery reads per pipeline, measured in #214.

decisions_reserved:
  - Shrinking or splitting the line-up seed.
  - Any change to the prod builds.

done_when:
  - tests/test_ci_data_job_invariants.py fails on main's .gitlab-ci.yml and passes on the branch.
  - The validate-local tier-1 gates pass.
  - validate:governance and test:python are green on the merge request.
  - After the merge, !310's data:build:mr builds fixture_lineup_corrections and its readers and assert_lineup_researched_matches_hold passes.

amendments: >
  none.
