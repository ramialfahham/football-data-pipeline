# Review — claude/task-folders-c4b70e — 2026-11-09

Rebound after the base moved to gitlab/main 2a45c5db: every reviewed blob is unchanged; only the deleted old shared task files are main's newer versions.

diff_sha256: 444d3d4a68e7f3c3088ad5761291b07a1d6217d5f1d2fdf8092333fab3891caa

rounds: 2

## scope-auditor
VERDICT: PASS
risks_checked:
- Round 1 FAIL on one line: docs/working_agreement.md:61 carried a rationale clause in a rule (§9). Round 2: the clause is cut; finding closed.
- Every changed file is in scope_paths, including the deleted old shared task artifacts; amendments are (none).
- protected_override names a dated approval; NEW MECHANISM and no recurring cost are declared in decisions_taken; no run, API call or reviewer row added.
- Doc-sync: hook behaviour change is mirrored in docs/agent_guardrails.md, working_agreement.md §2, the routing exclusions and all eight reviewer briefs.
- impact-map surface and approved_design: the diff touches no ingestion, dbt model, export script or site file; `none` holds.
- The merge order against the queued MRs stays in decisions_reserved, undecided in the diff.

## cto-reviewer
VERDICT: PASS
risks_checked:
- New mechanism (per-task folders, merged folders immutable, no old-layout path) declared in decisions_taken with its approval; no undeclared class, service, package or workflow step.
- Hooks still fail open on a bug; CI fails closed: resolver errors exit 1 before the artifact-only exemption, and a missing folder is an error.
- Routing changes only move the same five per-file exclusions to `.claude/task/*/<file>` patterns; artifact_only_never covers both contract paths; no routing row, model tier or required reviewer changed.
- CONTRACT_REL is now a message string only; every reader goes through _read_contract, so no gate reads a vanished fixed path.
- Briefs: path replacements only, no hunt item, verdict rule or model line weakened.
- No dependency, cost, secret or permission change; protected paths are in scope with protected_override and a concrete impact_map.
- Round 2 delta: only docs/working_agreement.md and tests/test_task_folders.py changed (blob-checked); round-1 conclusions stand.

## platform-reviewer
VERDICT: PASS
risks_checked:
- Round 1 FAIL: no test reached the commit gate's TASK FOLDER GATE branch (F1) or a shell write into `.claude/task/` (F2). Round 2: both pinned in tests/test_task_folders.py; reverting either branch now fails a test; findings closed.
- Resolver, gates and scripts are read-only and re-run safe; an interrupted run leaves no state.
- Local hook and CI call the same task_folder with errors before artifact-only; base and tip agree; hash exclusions read from one list.
- Review hash: per-folder patterns exclude exactly what the literal paths did, pinned against the real routing file; contract.md stays bound.
- Edge cases traced: merging main into a branch, squash merges, a folder renamed within a branch, the first file of a new task.
- Round 2 delta: only the two named files changed (blob-checked); no guard code moved.

## escalations
(none)
