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
| `git_discipline.py` | PreToolUse Bash | **Blocks** a real `gh pr merge` (the agent never merges); **blocks** `git commit --amend`/`--no-verify`/`-n` and `core.hooksPath` repointing (append-only, hook-verified history — governance G2); **nudges** the branch-consolidation questions on real branch creation. |
| `git_workflow.py` | PostToolUse Bash | After a real `git commit`, reminds: push with explicit refspec → open PR; not done until the PR URL exists. |
| `dbt_layer_gate.py` | PreToolUse Edit/Write/MultiEdit | When a `dbt_project/models/<layer>/*.sql` file is edited, injects that layer's contract *before* the wrong logic is written. Edit-time twin of `check_layer_contract.py`. Also covers the **consumption layer**: editing `scripts/export_*.py`, `site/` or `site_v2/` injects the frontend contract (no logic/transformation outside dbt — layering.md §Consumption layer). |
| `task_contract_gate.py` | PreToolUse Edit/Write/MultiEdit + Bash; PostToolUse Bash | The governance scope gate (working_agreement §2): **denies** repo edits with no task contract, edits outside `scope_paths`, edits to protected paths (`.claude/hooks/`, `.claude/agents/`, `.claude/commands/`, `.claude/settings.json`, `.claude/review_routing.json`, `.mcp.json`, `.cursor/mcp.json`, `.github/workflows/`) without `protected_override`, contract amendments on a dirty tree, and shell write-operators (`>`, `>>`, `tee`, `sed -i`, script heredocs) targeting out-of-scope repo files. After every Bash call it re-checks `git status` and injects a prescriptive reversion when out-of-scope changes appear. Paths outside the repo (memory, plans) are not governed. Fails open. |
| `stop_gate.py` | Stop | Turn-end net: if the tree does not match the contract, blocks the stop ONCE with revert instructions (`stop_hook_active` prevents loops). Guarantees nothing undeclared survives a turn even when the best-effort shell gates miss. |
| `git_discipline.py` (review gate, G3) | PreToolUse Bash on `git commit` | **Denies** the commit unless `.claude/task/review.md` exists, its `diff_sha256` equals the live staged-diff hash — computed over code **+** `contract.md` but EXCLUDING the `hash_exclude_paths` bookkeeping artifacts, so CI can recompute it from `git diff base...HEAD` and bind the review to the PR's code (F11/#409) — every reviewer required by `.claude/review_routing.json` for the staged paths has a verdict, no FAIL exists, every ESCALATE carries a `CPO ANSWER:` in its own section, and every PASS names ≥2 checked risks. Commit flags are **allowlisted** (`-m`/`--message`, `-F`/`--file`, `-q`, `-v`, `-S`/`--gpg-sign`, `-s`/`--signoff`): any other flag or positional pathspec is form-denied, because self-staging forms (`-a`/`-am`, `--include`, `--only`, `-p`, bundled `-qam`, abbreviated `--inc`) stage content after the hash was computed; git global options between `git` and `commit` (`git -p commit`, `git --git-dir x commit`) are denied outright — detection is token-loose, the allowed spelling is exactly `git commit`; the commit must be the SOLE command in its shell call (no `git add x && git commit` restaging after the hash check); the flag walk tokenizes the RAW command with shlex so a QUOTED pathspec cannot hide (unparseable quoting is denied); staged paths are enumerated NUL-split (`-z`) so quotePath-escaped names cannot drop a required reviewer; an ESCALATE before the first `##` header pairs in the `_preamble` pseudo-section. Artifact-only commits (`.claude/task/**`, `.claude/active_work.md`) exempt — EXCEPT any commit touching `contract.md` (`artifact_only_never`), which authorizes scope and is never review-exempt (F10/#409). `--staged-hash` CLI mode prints the live hash. The CI backstop `scripts/check_task_artifacts.py` recomputes the same hash from the branch diff and applies the same artifact/contract rules. |

### Reviewer subagents — `.claude/agents/` (committed, read-only tools)

The role briefs made executable (governance G3). Spawned cold in step 2 of the
review cycle; they judge the cumulative branch diff (`.claude/task/review_input.patch`)
against the contracts. Adversarial by construction: default FAIL, praise banned,
PASS requires ≥2 named risks, §10 decisions are never approved — only escalated.
Routing: `.claude/review_routing.json` (PROTECTED — changing who reviews what is a
CPO governance event). The agent definitions themselves are likewise PROTECTED
(CPO ruling, G3 escalation 2026-06-12) — the builder must not be able to weaken
its own adversary inside an ordinary task. Cast: `scope-auditor` (always, small model) +
`analytics-engineer-reviewer` (dbt/seeds/export cross-trigger) + the path-routed
specialists `cto-reviewer` (scripts/hooks/CI/deps), `data-engineer-reviewer`
(ingestion/registry-onboarding), `bi-analyst-reviewer` (wireframes/i18n/payload
shapes), `football-analytics-expert-reviewer` (catalogue formula edits). Defined
later, with their surfaces: ui-expert, data-journalist, legal-counsel (asset
policy). CFO/Growth/Product-Analyst are advisors (consulted at contract time),
not reviewers. **Model tiering** (CPO ruling 2026-06-12, pinned in each agent's
`model:` frontmatter): `scope-auditor` on **haiku**, the five specialists on
**sonnet**. The pin is a floor — for diffs touching a guard path
(`.claude/hooks/**`, `.claude/agents/**`, `.claude/commands/**`,
`.claude/settings.json`, `.claude/review_routing.json`,
`.mcp.json`, `.cursor/mcp.json`,
`.github/workflows/**`) the orchestrator spawns
`cto-reviewer` on **opus** (a procedural override, not hook-enforced), because
guard bypasses are the costliest misses.

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
| `handover_in.py` | SessionStart | Injects the project's `.claude/active_work.md` into every new chat so a fresh agent continues from the exact documented state instead of re-deriving (or silently re-scoping) it. The hard read-in half of the enforced handover. |
| `handover_plan_gate.py` | PreToolUse Edit/Write/MultiEdit | On the first code edit of a session where a handover exists, requires restating the locked spec and getting user approval before writing code. Fires once per session; skips edits to the handover file. The safety net that puts the user back in the loop before divergence becomes work. |
| `handover_out.py` | PreToolUse Bash | On a real `git push`, reminds to update `.claude/active_work.md` to reflect the new status. Keeps the handover current for the next session. (Reminder, not a hard block — a crying-wolf push block would get ignored.) |

No overlap between global and project hooks → no double-firing.

### The enforced handover — `.claude/active_work.md`

Continuity across chats is enforced, not hoped for. Each project keeps a single
**`.claude/active_work.md`** — a short, authoritative handover: current task, the
locked spec (or link), status (done / in-progress / next concrete action), and an
explicit **do-NOT** list. It is the *only* thing a fresh chat is guaranteed to read
(injected by `handover_in.py`). The loop:

- **Read-in (hard):** `handover_in.py` injects it at SessionStart — unavoidable.
- **Plan-back (safety net):** `handover_plan_gate.py` forces restate-and-approve before
  code, so a stale or misread handover is caught by the user before any work.
- **Write-out (kept current):** `handover_out.py` reminds on push to update it.

This exists because a fresh chat once re-scoped a fully-specified task (it read the
issue title + memory and built the wrong thing). Auto-loaded memory was not enough —
the handover must be a single focused file, pushed in, with the user as the gate.

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
