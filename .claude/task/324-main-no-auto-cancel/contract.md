# Task contract — a pipeline on main is never auto-cancelled by a newer commit

objective: >
  Issue 324: add `auto_cancel: on_new_commit: none` to the `workflow:rules` clause
  `if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH`, so every merge to main runs its own prod data build
  and nightly image deploy, and pin it with a test.

refs: >
  Issue 324. Approved in chat, 2026-11-16.

scope_paths:
  - .gitlab-ci.yml
  - tests/test_governance_hooks.py
  - .claude/task/324-main-no-auto-cancel/contract.md
  - .claude/task/324-main-no-auto-cancel/review.md
  - .claude/task/324-main-no-auto-cancel/review_input.patch

protected_override: >
  .gitlab-ci.yml edit approved in chat, 2026-11-16; the MR head declares the locked file.

impact_map: >
  writers: none; one key added to one `workflow:rules` clause.
  downstream: no model, seed or mart is touched; no dbt lineage affected. The key decides only
  whether GitLab cancels an older pipeline on the same ref when a newer one is created. The `main`
  clause is matched first by a push to main, a web run on main and a schedule (CI_COMMIT_BRANCH is
  set for all three), so all three stop being auto-cancelled. MR pipelines match the
  `merge_request_event` clause first and keep the default `conservative`. A web run on another
  branch matches the `web` clause and keeps the default too.
  layer_rules: not applicable, no model changes.
  deploy_order: none; takes effect for pipelines created after the merge. The older pipeline's
  own clause also carries the key, so whichever pipeline's setting GitLab reads, both say `none`.
  blast_radius: two merges close together now run two main pipelines in full instead of one. Each
  runs only the jobs its own `changes:` filters select, which is what each merge needs; the data
  jobs already queue on their resource group. No job sets `interruptible`, and no test pinned the
  absence of `auto_cancel`.

depends_on:
  - none: the change needs no open MR's code; !463 and !464 touch dbt models, not CI.

shared_files:
  - none: no design baseline, chart manifest or chart pin changes.

approved_design:
  - none: no page output changes

decisions_taken: >
  Add the one key, approved in chat, 2026-11-16. `none` rather than `interruptible`: both cancel
  nothing today, but `interruptible` would be reopened by a later `interruptible: true` default.
  No new mechanism and no new spend beyond running the builds each merge already needs.

decisions_reserved:
  - none: nothing else changes.

done_when:
  - The offline gates in FAST_GATES pass.
  - python -m pytest tests/ -q is green.
  - python scripts/ci_local.py --mr passes.
  - The MR pipeline is green and python scripts/merge_ready.py <IID> says ready.

amendments: (none)
