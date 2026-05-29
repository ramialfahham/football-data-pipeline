# Agent guardrails — hooks & skills

This repo encodes its working agreement not just as prose an agent *might* read,
but as **hooks** (deterministic, fire automatically at decision points) and
**skills** (procedures the agent runs on demand). This document explains what
exists, why, where it lives, and how to carry the portable parts to a new
project.

It exists because a commit-history audit (588 commits) showed **76 `fix`
commits vs 63 `feat` commits** — more time spent fixing than building — plus 12
reverts. The reverts clustered into: a layer violation (deduplication placed in
staging, across 73 models, later reverted), empty-payload-overwrites-warehouse
data bugs, metric-windowing errors, and a direct-push-to-main. The knowledge to
avoid all of these already existed in `docs/working_agreement.md` and the
memory `feedback_*` files. The failure was never *not knowing the rule* — it was
*not applying it at the moment of the decision*. **That gap — right rule, wrong
moment — is what hooks close.**

---

## When to use a hook vs a skill vs CI vs memory

| Mechanism | Fires | Best for | Limitation |
|---|---|---|---|
| **Hook** | Automatically, at a tool-call / plan / commit trigger | *Drift* — the agent knows the rule but doesn't apply it in the moment. Process gates. | Must be cheap and precise, or it becomes noise the agent tunes out. |
| **Skill** | When the agent chooses to invoke it (or is told) | A correct multi-step *sequence* (onboard, verify, validate-local). | Relies on the agent recognising the trigger. |
| **CI check** | At PR time, in CI | Authoritative invariants that must never merge broken. | Late — the wasted work already happened. |
| **Memory / docs** | Read by the agent | The knowledge itself. | Not enforcement — knowing ≠ doing. |

Rule of thumb: **prevention belongs in a hook** (catch before the work),
**a guarantee belongs in CI** (catch before the merge), **a procedure belongs in
a skill**, and **the reasoning belongs in docs/memory**. The strongest setup uses
several together — e.g. the dbt layer contract is a hook (edit-time prevention)
*and* a CI check (`scripts/check_layer_contract.py`, merge-time guarantee).

A hook that cries wolf is worse than no hook: the agent learns to ignore it.
Every Bash hook here is **self-gating** — it inspects the *actual* command and
only fires on a genuine match — precisely because the previous `if: Bash(...)`
matchers fired on unrelated read-only commands (`git log --grep=merge`, `cat`).

---

## What's installed

### Project hooks — `.claude/settings.json` → `.claude/hooks/*.py` (committed)

Project-specific wording (cite this repo's docs). Travel with the repo.

| Hook | Event / trigger | Does |
|---|---|---|
| `git_discipline.py` | PreToolUse Bash | **Blocks** a real `gh pr merge` (the agent never merges); **nudges** the branch-consolidation questions on real branch creation. |
| `git_workflow.py` | PostToolUse Bash | After a real `git commit`, reminds: push with explicit refspec → open PR; not done until the PR URL exists. |
| `dbt_layer_gate.py` | PreToolUse Edit/Write/MultiEdit | When a `dbt_project/models/<layer>/*.sql` file is edited, injects that layer's contract *before* the wrong logic is written. Edit-time twin of `check_layer_contract.py`. |

### Project skill — `.claude/skills/validate-local/` (committed)

`validate-local` runs the same gates CI runs, locally, before pushing — the
direct antidote to fix-after-CI churn. Tier 1 (fast/offline), Tier 2 (needs
BigQuery auth: dbt parse + sqlfluff), Tier 3 (full build/DQ — CI-only).

### Global hooks — `~/.claude/settings.json` → `~/.claude/hooks/*.py` (NOT in repo)

Project-agnostic. Apply to **every** project on this machine. Canonical copies
live in `docs/portable_guardrails/` so they can be version-controlled and copied
elsewhere.

| Hook | Event / trigger | Does |
|---|---|---|
| `plan_implement_gate.py` | PostToolUse ExitPlanMode | Right after a plan is approved: re-read the standards governing the files about to change; name the layer/module each change belongs in; hold to scope; plan to validate before pushing. |
| `pre_push_gate.py` | PreToolUse Bash | Before a real `git push`: run local validation first (avoid the CI round trip); confirm the push targets a feature branch, not main/master. |

No overlap between global and project hooks → no double-firing.

---

## Carrying the portable set to a new project

The two **global** hooks are generic. To set them up on a machine / for a new
project:

1. Copy the hook scripts into your global hooks dir:
   ```bash
   mkdir -p "$HOME/.claude/hooks"
   cp docs/portable_guardrails/hooks/*.py "$HOME/.claude/hooks/"
   ```
2. Merge the `hooks` block from `docs/portable_guardrails/settings.snippet.json`
   into `~/.claude/settings.json` (keep any existing `theme`, `enabledPlugins`,
   `permissions`, etc.). Validate: `python -m json.tool ~/.claude/settings.json`.
3. Done — they fire in every project automatically.

To give a **new project its own project-specific hooks**, copy the pattern in
`.claude/hooks/` here:
- Keep `_command_utils.py` (the self-gating helpers) — it's project-agnostic.
- Adapt `git_discipline.py` / `git_workflow.py` wording to that repo's docs (or
  drop them if the global set is enough).
- Replace `dbt_layer_gate.py` with whatever that project's structural contract is
  (e.g. a different layer/module layout), keying off the edited file's path.
- Register them in that project's `.claude/settings.json` (same shape as here).

### Requirements

- `python` must be on PATH in the hook shell (`shell: bash`). On Windows the
  bundled git-bash is used; `python` resolves there.
- Hooks **fail open**: any error or unparseable event exits 0 with no output, so
  a hook bug can never block your workflow.
- Changing `settings.json` may require approving the new hooks (a Claude Code
  safety prompt) or restarting the session before they take effect.

---

## Maintenance

- If a CI workflow adds/changes a gate, update `validate-local`'s gate list so it
  stays a faithful mirror.
- If a hook starts firing when it shouldn't, the fix is in the script's matcher
  (`.claude/hooks/_command_utils.py` `simple_commands` + the per-hook regex), not
  in a fragile `if:` glob.
- Keep `docs/portable_guardrails/hooks/*.py` in sync with `~/.claude/hooks/*.py`
  (the repo copy is canonical).
