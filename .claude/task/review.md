# Review — chore/retire-declaw-automation-g4 — 2026-06-13

> G4 audit cleanup: retire #410 (Slack-to-Executor bridge) + #411 (squad_watch.py),
> declaw #412 (ci-failure-watchdog.yml). Dispositions ruled by the CPO 2026-06-12 (audit
> table); §10 retire/declaw substance + two protected_overrides approved 2026-06-13
> ("as recommended", escalations.log). Required: scope-auditor (always) + cto-reviewer
> (scripts/** + .github/workflows/**). One cold iteration: both PASS against the hash below.
>
> Build note: during build two doc-sync consequences surfaced (the agent_company_roadmap
> index link to the deleted slack doc; the ci_failure_watchdog.md auto-rerun description).
> Scope was widened on a clean tree (contract amendment to add those two docs) BEFORE the
> reviewed commit, so the diff is doc-sync-complete. Repo-secret removal
> (CURSOR_EXECUTOR_BRIDGE_URL/TOKEN) is a CPO settings action, intentionally NOT in the diff.

diff_sha256: 8ae91d88ba7905796f90e3612cb92a961820fb311771846ca00faf615a827d6d

## scope-auditor
VERDICT: PASS
risks_checked:
- Authorization + §10 + protected paths: both protected paths
  (_paused/slack-executor-bridge.yml deletion, ci-failure-watchdog.yml edit) are named in
  the contract's protected_override block AND in scope_paths, and backed by the CPO ruling
  in escalations.log 2026-06-13 ("as recommended" for #410/#411/#412) with explicit
  justification that each exceeds the batch dead-trigger grant. No other protected path
  (.claude/hooks, .claude/agents, settings.json, review_routing.json, other workflows)
  touched. The two unrelated paused workflows (cursor-dispatch.yml, project-status-sync.yml)
  and the active workflows (pr-autopilot, pages, board-sync) are untouched. No decision taken
  beyond the CPO ruling.
- Scope discipline + surgical #412: every changed file is in scope_paths; the watchdog edit
  changed only the auto-rerun step + `actions: write` permission + the now-false body/Next-action
  text — the watched-workflow list, issue title, and dedup logic are unchanged.
- Doc-sync completeness: repo-wide search confirms no remaining reference to the slack bridge
  scripts/workflow or squad_watch, and no doc still claims the watchdog auto-reruns, outside
  the historical audit record (docs/audits/2026-06_alignment_audit.md, correctly left as-is).
  The agent_company_roadmap index link to the deleted slack doc is removed (no dangling link);
  chat_driven_workflow.md + ci_failure_watchdog.md updated to notification-only.
- decisions_reserved: secret removal is NOT done in the diff (correctly left to the CPO).
escalations:
- (none)

## cto-reviewer
VERDICT: PASS
risks_checked:
- Watchdog integrity after rerun excision: all five variables used after the deleted block
  (runUrl, attempt, branch, workflowName, actor) remain defined; `rerunTriggered` is gone from
  BOTH the logic and the issue body line that referenced it; the rerun API call is fully
  removed; braces/template literals balanced; YAML valid.
- Permission narrowing correct + complete: `actions: write` was required ONLY by the deleted
  rerun-failed-jobs request; the remaining ops (issues.listForRepo, issues.create,
  issues.createComment) are all covered by the retained `issues: write` (+ `contents: read`
  baseline). Nothing remaining needs actions:write; nothing remaining lacks a permission.
- Deletion blast radius: scripts/slack_bridge/, squad_watch.py, and the paused workflow are
  fully absent; grep finds zero live references to slack_bridge/slack_executor/squad_watch/
  CURSOR_EXECUTOR outside .claude/task/ and the historical audit doc; no 404-producing
  markdown link remains.
- Surgical scope: the trigger workflow list, issueTitle template, dedup predicate, and
  paginate call are byte-identical to pre-patch; only the rerun step + permission + body text
  differ. Unrelated paused + active workflows untouched.
- Guard integrity: contract carries explicit protected_override for both protected paths with
  traceable CPO approval (escalations.log 2026-06-13); justification for each override recorded.
escalations:
- (none)

## escalations
(none — single cold iteration; both reviewers PASS against the locked hash. The two doc-sync
files were added to scope via a clean-tree contract amendment before the reviewed commit.
Repo secrets CURSOR_EXECUTOR_BRIDGE_URL/TOKEN remain for the CPO to remove in GitHub settings,
outside the tree.)
