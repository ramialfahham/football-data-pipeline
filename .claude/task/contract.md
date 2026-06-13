# Task contract — retire #410/#411 + declaw #412 (G4 audit cleanup)

> Retire two never-approved automation relics and declaw a live over-permissioned
> watchdog, per the G4 audit (F16/#410, F17/#411, F19/#412). Dispositions ruled by the
> CPO 2026-06-12 (audit table) and the §10 retire/declaw SUBSTANCE + two protected_overrides
> approved 2026-06-13 ("as recommended", see escalations.log). One PR (shared grant,
> identical reviewer routing). See docs/working_agreement.md §2/§10.

objective: >
  #410 (F16) — FULL RETIRE the paused Slack-to-Executor bridge (a never-approved A3
  mechanism, already paused, no active trigger): delete the three scripts under
  scripts/slack_bridge/, docs/slack_executor_bridge.md, the bridge line in
  docs/chat_driven_workflow.md's paused list, AND the paused workflow file
  .github/workflows/_paused/slack-executor-bridge.yml (PROTECTED — explicit
  protected_override, escalations.log 2026-06-13). Repo secrets
  CURSOR_EXECUTOR_BRIDGE_URL/TOKEN are removed by the CPO in settings (outside the tree).
  #411 (F17) — RETIRE scripts/squad_watch.py (un-budgeted WC API-volume relic; no callers).
  #412 (F19) — DECLAW the LIVE .github/workflows/ci-failure-watchdog.yml (PROTECTED —
  explicit protected_override): remove the auto-rerun-failed-jobs step, DROP the
  `actions: write` permission, KEEP the [CI Failure] issue open/comment notification
  (`issues: write` + `contents: read`). Update the watchdog behaviour text in
  docs/chat_driven_workflow.md to match (notification-only, no auto-rerun).

refs: audit F16/#410, F17/#411, F19/#412; docs/audits/2026-06_alignment_audit.md ruling table.

protected_override:
  approval: CPO, 2026-06-13 ("as recommended" for #410/#411/#412 — escalations.log entry
    "chore/retire-declaw-automation-g4"). Two explicit overrides beyond the batch
    dead-trigger grant:
  - .github/workflows/_paused/slack-executor-bridge.yml  # #410: delete the whole paused workflow (more than a trigger)
  - .github/workflows/ci-failure-watchdog.yml            # #412: edit a LIVE workflow's logic + narrow its permissions

scope_paths:
  - scripts/slack_bridge/forward_to_executor.py
  - scripts/slack_bridge/normalize_brief.py
  - scripts/slack_bridge/post_thread_update.py
  - scripts/squad_watch.py
  - .github/workflows/_paused/slack-executor-bridge.yml
  - .github/workflows/ci-failure-watchdog.yml
  - docs/slack_executor_bridge.md
  - docs/chat_driven_workflow.md
  - docs/ci_failure_watchdog.md
  - docs/agent_company_roadmap.md
  - .claude/task/contract.md

decisions_taken: >
  Dispositions + the two protected_overrides are CPO-approved (escalations.log 2026-06-13,
  "as recommended"). #410/#411 are deletions of never-approved/un-budgeted relics; #412 keeps
  the useful failure-notification and drops only the unapproved auto-rerun + its broad
  `actions: write` scope (also removes the flaky-failure-masking behaviour). No behaviour
  change to any KEPT automation. Other paused workflows (cursor-dispatch.yml, pr-autopilot.yml,
  project-status-sync.yml) and the active pr-autopilot/pages/board-sync are OUT of scope.

decisions_reserved:
  - Repo-secret removal (CURSOR_EXECUTOR_BRIDGE_URL/TOKEN) is a CPO settings action, NOT done here.
  - Keep it surgical: retire exactly the named #410/#411 assets; for #412 change ONLY the
    auto-rerun step + the `actions: write` permission + the matching doc/body text — do NOT
    alter the watched-workflow list, the issue title/dedup logic, or the notification body
    beyond removing the now-false "auto-rerun" line. Do NOT touch any other workflow or the
    two unrelated paused workflows. If a reviewer finds a kept automation would break, STOP.

done_when:
  - #410: the 3 slack_bridge scripts, docs/slack_executor_bridge.md, and
    _paused/slack-executor-bridge.yml are deleted; the bridge entry is gone from
    chat_driven_workflow.md's paused list AND its index link is removed from
    docs/agent_company_roadmap.md; no remaining repo reference to the slack bridge
    scripts/workflow (the historical audit record + secrets-in-settings excepted).
  - #411: scripts/squad_watch.py is deleted; no remaining caller.
  - #412: ci-failure-watchdog.yml no longer reruns jobs and no longer declares
    `actions: write`; it still opens/comments the [CI Failure] issue (`issues: write`,
    `contents: read`); the issue body no longer claims an auto-rerun; chat_driven_workflow.md's
    watchdog behaviour text AND docs/ci_failure_watchdog.md match (notification-only, no
    auto-rerun). The workflow still parses (valid YAML).
  - reviewers: scope-auditor (always) + cto-reviewer (scripts/** + .github/workflows/**) — PASS.

amendments: (none)
