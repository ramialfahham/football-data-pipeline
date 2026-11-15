# Task contract — the full design sweep on main gets a 2h job timeout

objective: >
  Issue 315: give the `validate:ui` job an explicit `timeout: 2h`. Main's full sweep runs 41–60 min
  and the 1h project default killed a passing sweep on main pipeline 3070873799.

refs: >
  Issue 315. Approved in chat, 2026-11-15.

scope_paths:
  - .gitlab-ci.yml
  - .claude/task/315-validate-ui-timeout/contract.md
  - .claude/task/315-validate-ui-timeout/review.md
  - .claude/task/315-validate-ui-timeout/review_input.patch

protected_override: >
  .gitlab-ci.yml edit approved in chat, 2026-11-15; the MR head declares the locked file.

impact_map: >
  writers: none; one key added to the validate:ui job.
  downstream: no model, seed or mart is touched; no dbt lineage affected. No later job `needs`
  validate:ui (`grep -n "validate:ui" .gitlab-ci.yml` lists only the job itself).
  layer_rules: not applicable, no model changes.
  deploy_order: none; takes effect on the next pipeline. The data jobs in the same file already set
  `timeout: 2h`.
  blast_radius: a validate:ui run may now hold a runner slot up to 2h instead of 1h before GitLab
  kills it. The merge-request scope (2 widths, 2 languages, plus fi at 320) is unaffected in
  practice. No test in tests/ pins the job's timeout or its key set.

approved_design:
  - none: no page output changes

decisions_taken: >
  Add the one key, approved in chat, 2026-11-15. No new mechanism and no new spend: the runner is
  self-hosted, and a longer limit only lets an already-running sweep finish.

decisions_reserved:
  - none: nothing else changes.

done_when:
  - The offline gates in FAST_GATES pass.
  - python -m pytest tests/ -q is green.
  - The MR pipeline is green.

amendments: (none)
