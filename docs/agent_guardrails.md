# Agent guardrails — hooks & skills

The working agreement is enforced, not only written: **hooks** fire automatically at decision
points, **skills** are procedures the agent runs on demand. This document lists what exists and
where it lives. The rules the hooks enforce are [`working_agreement.md`](working_agreement.md);
each hook's docstring has its exact behaviour.

---

## Hook, skill, CI or docs

| Mechanism | Fires | Best for | Limitation |
|---|---|---|---|
| **Hook** | Automatically, at a tool call, plan or commit | *Drift*: the agent knows the rule but does not apply it in the moment | Must be cheap and precise, or it becomes noise the agent tunes out |
| **Skill** | When the agent invokes it | A correct multi-step sequence | Relies on the agent recognising the trigger |
| **CI check** | On every MR pipeline | Invariants that must never merge broken | Late: the wasted work already happened |
| **Docs / memory** | When the agent reads them | The knowledge itself | Not enforcement |

Every Bash hook is **self-gating**: it inspects the actual command and fires only on a genuine
match, because a hook that cries wolf gets ignored.

---

## Project hooks — `.claude/settings.json` → `.claude/hooks/` (protected)

| Hook | Fires on | Does |
|---|---|---|
| `git_discipline.py` | PreToolUse Bash | Blocks `glab mr merge`, `git commit --amend`/`--no-verify`/`-n` and `core.hooksPath` repointing; asks the branch-consolidation questions on branch creation. On `git commit` it is the **review gate**: denies the commit unless the review cycle passed and `.claude/task/review.md` is bound to the staged diff (`working_agreement.md` §2). On a diff touching `site_v2/src/` it also requires the contract's `acceptance_criteria:`, each demonstrated in `.claude/task/acceptance_evidence.md`. `scripts/check_task_artifacts.py` repeats the check in CI. |
| `git_workflow.py` | PostToolUse Bash | After a commit, reminds: push the feature branch, open the MR. |
| `task_contract_gate.py` | PreToolUse Edit/Write/MultiEdit/NotebookEdit, Bash, Artifact; PostToolUse Bash | Denies an edit with no task contract or outside `scope_paths`. Denies an edit on a protected path without `protected_override`, or on the structural surface without an `impact_map`. Denies a shell write to an out-of-scope file, and an `Artifact` publish without a real `decisions_reserved`. After every Bash call, it names the out-of-scope changes to revert. The rules are `working_agreement.md` §2. |
| `dbt_layer_gate.py` | PreToolUse Edit/Write/MultiEdit/NotebookEdit | Injects the layer contract when a dbt model or a consumption file (`scripts/export_*.py`, `site/`, `site_v2/`) is edited. `scripts/check_layer_contract.py` enforces it in CI. |
| `comment_history_gate.py` | PreToolUse Edit/Write/MultiEdit/NotebookEdit | Denies an edit that adds history to a code comment or a Markdown document. History is a date, an issue or MR number, a review credit or round, or a story phrase. `tests/test_no_decision_history_in_code.py` and `tests/test_no_decision_history_in_docs.py` pin the lines left; the counts only go down. |
| `memory_budget_gate.py` | PreToolUse Edit/Write/MultiEdit/NotebookEdit | Denies a write that takes the memory folder over its budget (`CLAUDE.md`, "Memory files"). `--report` shows where it stands. |
| `host_fingerprint_gate.py` | PreToolUse Edit/Write/MultiEdit/NotebookEdit | Denies a public network address in any repo file. `tests/test_no_host_fingerprint_in_tree.py` keeps the tree at zero. |
| `tracker_snapshot_gate.py` | PreToolUse Edit/Write/MultiEdit/NotebookEdit | Denies every edit under `docs/tracker/`; only `scripts/snapshot_tracker.py` writes the tracker backup. |
| `stop_gate.py` | Stop | Blocks the end of a turn once when the tree does not match the contract or an offline gate in `FAST_GATES` fails. |
| `handover_in.py` | SessionStart | Injects the handover issue into every session, from GitLab or, when GitLab is down, from `.claude/handover.cache.md`. Capped at 16,000 characters; says when it truncates. The handover is rewritten at the end of every session (`CLAUDE.md`). |

Hooks fail open: an error or an unreadable event lets the call through. The review gate is the
exception: when it cannot resolve the base branch, it denies.

## Reviewer agents — `.claude/agents/` (protected)

Read-only agents, spawned cold in step 2 of the review cycle (`working_agreement.md` §2). Each
judges the cumulative branch diff in `.claude/task/review_input.patch` and starts from the
assumption that there is a defect. Which agent reviews which path is
`.claude/review_routing.json`; each agent's model is its `model:` line.

| Agent | Reviews |
|---|---|
| `scope-auditor` | every commit: the diff against the contract, §10 classes, secrets, undeclared thresholds |
| `analytics-engineer-reviewer` | dbt models and seeds, export data handling |
| `platform-reviewer` | scripts, tests, hooks, CI, dependencies, the site build and hosting |
| `data-engineer-reviewer` | ingestion, competition onboarding, the data contract |
| `bi-analyst-reviewer` | wireframes, `site_v2/src/**`, `site/i18n/**` |
| `football-analytics-expert-reviewer` | `metric_catalogue.csv` |
| `cto-reviewer` | a new mechanism, a dependency, a guard invariant, a recurring cost |
| `seo-expert-reviewer` | nothing: not routed |

## Project skills — `.claude/skills/`

| Skill | Use |
|---|---|
| `validate-local` | the CI gates, run locally before a push |
| `onboard-competition` | add a competition: registry entry, dbt vars sync, labels |
| `onboard-endpoint` | evaluate and ingest a new provider endpoint, cost approved first |
| `verify-competition-ingest` | check a competition's ingest health |

The `/status` command (`.claude/commands/status.md`, protected) shows the branch, the tree, open
MRs and the handover.

---

## Portable hooks — `docs/portable_guardrails/`

Five generic hooks for a user-level install in `~/.claude/hooks/`. None is installed on this
machine.

| Hook | Fires on | Would do |
|---|---|---|
| `plan_implement_gate.py` | PostToolUse ExitPlanMode | After a plan is approved, inject a checklist against scope drift |
| `pre_push_gate.py` | PreToolUse Bash | Before `git push`, remind to validate locally first |
| `handover_plan_gate.py` | PreToolUse Edit/Write/MultiEdit | On a session's first code edit, require the handover's spec restated and approved |
| `handover_out.py` | PreToolUse Bash | On `git push`, remind to update the handover |
| `handover_in.py` | SessionStart | An older copy of the project hook; use `.claude/hooks/handover_in.py` |

The three handover hooks read a `.claude/active_work.md` file, which this project does not use.

To install them:

1. `cp docs/portable_guardrails/hooks/*.py "$HOME/.claude/hooks/"`
2. Merge the `hooks` block of `docs/portable_guardrails/settings.snippet.json` into
   `~/.claude/settings.json`. In a project with its own `handover_in.py`, like this one, drop the
   `SessionStart` entry, or the handover is injected twice.
3. `python -m json.tool ~/.claude/settings.json`

Hooks run with `python` on PATH in a bash shell (git-bash on Windows). A changed `settings.json`
may need the hooks approved or the session restarted.

## Maintenance

- A gate added to or changed in `.gitlab-ci.yml` is added to or changed in `validate-local`.
- A hook that fires when it should not is fixed in its matcher: `.claude/hooks/_command_utils.py`
  and the hook's own pattern. An `if:` glob in `settings.json` is never the fix.
