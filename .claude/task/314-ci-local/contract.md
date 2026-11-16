# Task contract — one local CI command

objective: >
  Issue 314, step 2: scripts/ci_local.py runs any job of .gitlab-ci.yml (--job <name>) or every offline job a merge
  request pipeline would run for the changed files (--mr), in the job's own image, in a clean checkout of the merged
  result, with only the artifacts its needs: name. Data jobs run dbt parse and sqlfluff lint, never dbt build and
  never a BigQuery write. The validate-local skill becomes this one command, run before every push.

refs: >
  Issue 314 (step 2 of its How, after !445). Requested by the coordinating session. Go-live gate: issue 290.

depends_on: none  # built on gitlab/main; the one-command script needs no open MR (!449 is merged)

shared_files: none  # no design baseline, chart manifest or pin is touched

scope_paths:
  - scripts/ci_local.py
  - tests/test_ci_local.py
  - .claude/skills/validate-local/SKILL.md
  - .claude/task/314-ci-local/contract.md
  - .claude/task/314-ci-local/review.md
  - .claude/task/314-ci-local/review_input.patch

approved_design:
  - none: no page output changes

decisions_taken: >
  A new local-only script, no change to .gitlab-ci.yml and no recurring cost. It reads the CI file at run time and
  keeps no copy of a step. scripts/validate_ui_docker.py (!445) is left in place and untouched. The merged result is
  built in a throwaway clone with LF endings, where origin/main is the fetched gitlab/main, so check_task_artifacts
  sees the same base as CI. Data jobs (id_tokens, or stage data) are replaced by dbt parse plus sqlfluff lint; jobs
  that deploy or need a cloud credential are skipped and named in the output.

decisions_reserved:
  - none: the command and its output are developer tooling, nothing fan-visible, nothing permanent once published.

done_when:
  - tests/test_ci_local.py covers changes: matching, needs: artifacts, extends and anchors, rule evaluation, the merged-result step, data-job substitution.
  - Full pytest is green before every review round.
  - python scripts/ci_local.py --mr on this branch ends with every selected job green.
  - The MR pipeline is green.

amendments: (none)
