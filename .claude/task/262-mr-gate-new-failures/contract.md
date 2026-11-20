# Task contract — a merge request's data build tests only what the merge request changes

objective: >
  `data:build:mr` stops running the separate full singular suite against prod. A merge request is
  tested by the tests inside its own lineage build (`state:modified+` plus the seeds it changed), so
  a failure prod already has can no longer turn an unrelated merge request red. The full test suite
  runs in `data:build:main` and the nightly only.

refs: >
  #262; the 20 Nov 2026 prod nightly failure (two wrong singular tests, fixed in !492) that left
  `data:build:mr` red on every merge request; !491, !492, !493.

scope_paths:
  - .claude/task/262-mr-gate-new-failures/
  - .gitlab-ci.yml
  - tests/test_ci_data_job_invariants.py
  - dbt_project/docs/layering.md
  - dbt_project/tests/assert_metric_meaning_complete.sql

protected_override: >
  Removing the separate singular-test step from `data:build:mr` in `.gitlab-ci.yml`: approved in
  chat, 2026-11-20.

impact_map: >
  writers: none; no table, model or page output changes.
  guard: `data:build:mr` loses its last script line, `dbt test --select test_type:singular ...`.
  The lineage `dbt build` before it is unchanged and still runs every test on the models and seeds
  the merge request touches and their descendants (measured on MR 491, job 18212969580: one seed
  selected 1423 tests and 87 models in the build, and a singular test failed inside it).
  readers: tests/test_ci_data_job_invariants.py is the only file that parses the job's `dbt test`
  line (`_mr_dbt_invocations`, now `_dbt_lines`); `grep -rnE "dbt test|test_type" tests scripts docs
  .claude/hooks dbt_project` finds one other reader, the comment of
  dbt_project/tests/assert_metric_meaning_complete.sql, which is rewritten here. scripts/ci_local.py runs data:build:mr offline only
  (dbt parse and sqlfluff lint, no dbt test); scripts/merge_ready.py reads it through ci_local. `data:build:main` (`dbt test --select test_type:singular ... --target
  prod`) and the nightly are not edited.
  failure: a merge request that changes a model no longer runs singular tests that read only
  unmodified nodes; they run on main after the merge and in the nightly. A red test on main is then
  the signal, as for any other post-merge failure. Cost: about 15.65 GB (about $0.10) and 2 minutes
  per merge request pipeline are no longer spent (measured on MR 491, job 18203321659).
  blast_radius: CI behaviour and cost of `data:build:mr` only; no data, no deploy.

approved_design:
  - none: no page output changes

depends_on:
  - none: works on main alone

shared_files:
  - none: no design, registry, font or chart baseline changes

decisions_taken: >
  The rule that a merge request is tested only on what it changes, and that the full suite runs in
  `data:build:main` and the nightly, is approved in chat, 2026-11-20. The stale comments and the
  layering paragraph that describe the removed step are rewritten to the current rule, one line
  each. No new dependency, mechanism or recurring cost.

decisions_reserved:
  - none: the rule, the removal and the wording scope are the approved instruction.

done_when:
  - python -m pytest tests/test_ci_data_job_invariants.py -q passes, with a test that data:build:mr runs no `dbt test` and keeps the lineage build, and a test that data:build:main runs the full singular suite.
  - grep -rn "full singular suite always runs" .gitlab-ci.yml dbt_project/docs returns nothing.
  - python scripts/ci_local.py --mr is green.
  - The merge request pipeline is green and python scripts/merge_ready.py <iid> says ready.

amendments: (none)
