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
| `git_discipline.py` | PreToolUse Bash | **Blocks** a real `glab mr merge` (the agent never merges); **blocks** `git commit --amend`/`--no-verify`/`-n` and `core.hooksPath` repointing (append-only, hook-verified history — governance G2); **nudges** the branch-consolidation questions on real branch creation. |
| `git_workflow.py` | PostToolUse Bash | After a real `git commit`, reminds: push with explicit refspec → open MR; not done until the MR URL exists. |
| `dbt_layer_gate.py` | PreToolUse Edit/Write/MultiEdit | When a `dbt_project/models/<layer>/*.sql` file is edited, injects that layer's contract *before* the wrong logic is written. Edit-time twin of `check_layer_contract.py`. Also covers the **consumption layer**: editing `scripts/export_*.py`, `site/` or `site_v2/` injects the frontend contract (no logic/transformation outside dbt — layering.md §Consumption layer). |
| `task_contract_gate.py` | PreToolUse Edit/Write/MultiEdit + **Artifact** + Bash; PostToolUse Bash | The governance scope gate (working_agreement §2): **denies** repo edits with no task contract, edits outside `scope_paths`, edits to protected paths (`.claude/hooks/`, `.claude/agents/`, `.claude/commands/`, `.claude/settings.json`, `.claude/review_routing.json`, `.mcp.json`, `.cursor/mcp.json`, `.github/workflows/`, `.gitlab-ci.yml`) without `protected_override`, contract amendments on a dirty tree, edits on the **structural surface** when the contract carries no non-placeholder `impact_map` (§2 / Appendix A6 — trace before code), and shell write-operators (`>`, `>>`, `tee`, `sed -i`, script heredocs) targeting out-of-scope repo files. After every Bash call it re-checks `git status` and injects a prescriptive reversion when out-of-scope changes appear. Paths outside the repo (memory, plans) are not governed. Fails open. **Two additions 2026-07-22:** (a) the **protected paths are now part of the structural surface**, so a guard edit needs `protected_override` *and* an `impact_map` — authority and understanding are different questions, and a guard's blast radius is every future task in the repo. This is enforced on the Edit path *and* the shell path. (b) an **`Artifact` publish is denied when no contract exists**. Design was the only surface with no gate at all — a mock is written outside the repo, so every path-keyed check returned before reaching it — and it is the surface that failed three times in one day. The gate cannot ask "is this path in scope"; it asks two questions it can answer honestly — does a contract exist, and does it carry a **real** `decisions_reserved` rather than the template's bare `- none`. The second is what gives the gate teeth: a contract is mandatory before any repo edit, so one exists in nearly every session, and contract-existence alone would make this fire almost never. "Nothing is open" remains a legitimate answer, stated as a checkable sentence. |
| `comment_history_gate.py` | PreToolUse Edit/Write/MultiEdit | **Denies** an edit whose written text adds, to a code file, a comment line carrying decision history — a date, "CPO", a review credit (a named role — `platform-reviewer`, `scope-auditor` — or what an unnamed reviewer did: "a reviewer caught it", "two reviewers failed it", "found by a reviewer"; the bare word alone is the review gate's own vocabulary and is not a marker), "round N" or an MR number — and says where that belongs: the commit message, the MR and the issue, reached from any line by `git blame` (`engineering_standards.md` §1.2). A comment line is one with a marker (`#`, `--`, `//`, `/*`, `*`, `<!--`, `{#`) at its start or after whitespace, any line inside a block comment of the file's language (`/* … */`, `<!-- … -->`, `{# … #}`), and any line of a Python docstring (`ast` on a whole file; a line opening with a triple quote in an edit fragment). A quoted span on the line (`"CPO ANSWER:"`, a `'2026-05-07 17:55:00'` usage example) is a literal and is blanked before matching; an apostrophe inside a word opens no span, a triple quote is a docstring delimiter, and backticks are NOT literals — measured over the tree, two in three backticked markers were credits. Checks only the text being written, so an edit that re-includes an existing flagged line is denied until the marker goes — every ordinary edit helps the sweep. Markdown, docs, `.claude/task/` and unlisted trees are never checked. Its twin in CI, `tests/test_no_decision_history_in_code.py`, imports the hook's own pattern and tree list and pins the count of flagged lines already in the tree in BOTH directions, so a sweep must lower the pin and the number never moves silently. Fails open. |
| `stop_gate.py` | Stop | Turn-end net: if the tree does not match the contract, blocks the stop ONCE with revert instructions (`stop_hook_active` prevents loops). Guarantees nothing undeclared survives a turn even when the best-effort shell gates miss. |
| `handover_in.py` | SessionStart | Injects `.claude/active_work.md` into every new chat so a fresh agent continues from the documented state instead of re-deriving (or silently re-scoping) it, and says so explicitly when the file is missing. Announces truncation rather than cutting in silence. **Was a *global* hook and was therefore never actually running** — no `SessionStart` key existed in `.claude/settings.json`, `.claude/settings.local.json`, or the user-level settings, while the handover claimed it did. Moved into the project's protected hooks directory and wired here on 2026-07-22, because a script that auto-executes every session is guard-class and must not sit on an unprotected, unrouted path (the `.claude/commands/` and `.mcp.json` rulings). |
| `git_discipline.py` (review gate, G3) | PreToolUse Bash on `git commit` | **Denies** the commit unless `.claude/task/review.md` exists, its `diff_sha256` equals the live hash — computed over code **+** `contract.md` but EXCLUDING the `hash_exclude_paths` bookkeeping artifacts, so CI can recompute it and bind the review to the PR's code (F11/#409). ⚠ Since **#63** the hashed bytes are `git diff --raw` (mode, blob SHAs, status, path) taken CUMULATIVELY FROM THE BASE, not the rendered patch of a bare `--staged`: a rendered patch is a presentation format whose bytes vary with git version, platform and diff settings, so the local gate and the CI recompute disagreed about identical commits and `validate:governance` could not pass at all. Blob SHAs are content hashes, so the two halves now agree everywhere and on a branch of any length. Nothing is weakened — the rendered patch is DERIVED from those blobs and cannot differ unless one does. ⚠ If the base cannot be resolved the hash is not computed at all, and BOTH halves say so instead of inventing a value: `--staged-hash` exits non-zero with a stderr reason, and the gate denies with its own message. An earlier draft of #63 returned `b""` here and called that fail-closed — it was the opposite, and two opus reviewers found it independently: `--staged-hash` printed `sha256(b"")` with exit 0, that value went into `review.md`, the gate recomputed the same empty value from the same broken call, the two AGREED, and the commit passed bound to ZERO bytes. Reproduced, then fixed, then pinned by `test_staged_hash_refuses_to_emit_a_hash_it_could_not_compute` and `test_commit_gate_denies_when_the_hash_cannot_be_computed`. ⚠ This is a deliberate DEPARTURE from the file's fail-open house rule, and the narrow case where it is right: an unresolvable base is not a hook bug, it is the guard being unable to do its job, and the deny message is actionable (fetch the base branch, or set `GOVERNANCE_BASE`) — every reviewer required by `.claude/review_routing.json` for the staged paths has a verdict, no FAIL exists, every ESCALATE carries a `CPO ANSWER:` in its own section, every PASS names ≥2 checked risks, and a `rounds:` line is present, a positive integer, and within the cap of 3 (past the cap needs `rounds_cap_override:` — the loop is bounded, review-economics 2026-07-22). Commit flags are **allowlisted** (`-m`/`--message`, `-F`/`--file`, `-q`, `-v`, `-S`/`--gpg-sign`, `-s`/`--signoff`): any other flag or positional pathspec is form-denied, because self-staging forms (`-a`/`-am`, `--include`, `--only`, `-p`, bundled `-qam`, abbreviated `--inc`) stage content after the hash was computed; git global options between `git` and `commit` (`git -p commit`, `git --git-dir x commit`) are denied outright — detection is token-loose, the allowed spelling is exactly `git commit`; the commit must be the SOLE command in its shell call (no `git add x && git commit` restaging after the hash check); the flag walk tokenizes the RAW command with shlex so a QUOTED pathspec cannot hide (unparseable quoting is denied); staged paths are enumerated NUL-split (`-z`) so quotePath-escaped names cannot drop a required reviewer; an ESCALATE before the first `##` header pairs in the `_preamble` pseudo-section. Artifact-only commits (`.claude/task/**`, `.claude/active_work.md`) exempt — EXCEPT any commit touching `contract.md` (`artifact_only_never`), which authorizes scope and is never review-exempt (F10/#409). `--staged-hash` CLI mode prints the live hash. The CI backstop `scripts/check_task_artifacts.py` recomputes the same hash from the branch diff and applies the same artifact/contract rules. **Acceptance gate (CPO ruling 2026-07-31, #868):** on a diff touching `site_v2/src/` — and ONLY there, so it cannot cry wolf on warehouse or tooling work — the commit is also denied unless `contract.md` declares `acceptance_criteria:` and `.claude/task/acceptance_evidence.md` demonstrates every one of them under a `criteria_demonstrated:` marker, read from BUILT output. Evidence lines must be substantive and distinct: a count alone is satisfied by two bullets both reading "checked". This is the QA function, and it is an artifact plus a gate rather than a reviewer agent because the check needs proof, not judgement. |
| `memory_budget_gate.py` | PreToolUse Edit/Write/MultiEdit/NotebookEdit on `~/.claude/projects/<slug>/memory/*.md` | **Denies** a write to the agent's memory folder when the RESULTING file would exceed its surface's budget — the index `MEMORY.md`, or any other note — or when a new note would push the count past the cap: adding a note means removing one. Measures the file the tool call will produce (a `Write`'s content; an `Edit` or `MultiEdit` applied to the file on disk), in characters; a result no larger than the file on disk always passes, so an over-budget note can always be cut. The three budgets are pinned to what the folder MEASURED after the cut that introduced them (50 notes, a 7,669-character index, a 4,232-character largest note) and move down only — the same shape as the comment guard's pinned count. Memory is the one surface no other gate looks at (`task_contract_gate.py` deliberately ignores paths outside the repo), and it is where two 2026-09 sessions took a product fact the repo contradicted; a budget is what makes the cut hold. `--report` prints the three measurements; `tests/test_memory_budget_gate.py` drives every deny and pass on a temp folder. A shell write into the folder bypasses it, as it bypasses the comment gate; the repo's rule already forbids shell writes for files. |

### Reviewer subagents — `.claude/agents/` (committed, read-only tools)

The role briefs made executable (governance G3). Spawned cold in step 2 of the
review cycle; they judge the cumulative branch diff (`.claude/task/review_input.patch`,
generated by `git_discipline.py --review-patch`, which excludes the review's own
paperwork — see `review_exclude_paths`) against the contracts. Adversarial by
construction: start from the assumption there is a defect, praise banned, §10
decisions are never approved — only escalated. **A FAIL must name a defect; a PASS
must say what it examined and may find nothing** (CPO 2026-08-01, after the two-risk
rule obliged reviewers to invent findings on correct code).
Routing: `.claude/review_routing.json` (PROTECTED — changing who reviews what is a
CPO governance event). The agent definitions themselves are likewise PROTECTED
(CPO ruling, G3 escalation 2026-06-12) — the builder must not be able to weaken
its own adversary inside an ordinary task. Cast: `scope-auditor` (always, small model) +
`analytics-engineer-reviewer` (dbt/seeds/export cross-trigger) + the path-routed
specialists `platform-reviewer` (the machinery: scripts, tests, hooks, CI, deps,
site build + hosting), `data-engineer-reviewer`
(ingestion/registry-onboarding), `bi-analyst-reviewer` (wireframe specs, the
whole built frontend `site_v2/src/**` — CPO ruling 2026-07-22, because the
binding rule is written in the spec and broken on the page — and `site/i18n/`;
it READS the export to verify bindings but does not review it),
`football-analytics-expert-reviewer` (catalogue formula edits) + `cto-reviewer`,
which after the **CTO split (CPO ruling 2026-07-31, #868)** owns NO territory
and is woken by a PROPERTY of the change: a new mechanism, a new dependency, a
guard invariant, a recurring cost. Two of those four are path-detectable and
routed; two can appear in any file and reach it only via the contract's
`decisions_taken:`, with the always-on `scope-auditor` as the tripwire. Before
the split the CTO was required on 28% of commits and 48 tracked files pulled in
both it and the display reviewer, so a CTO reviewed Astro markup. Defined
later, with their surfaces: ui-expert, data-journalist, legal-counsel (asset
policy). `seo-expert-reviewer` exists but is STILL NOT ROUTED — approved in
principle 2026-07-31, not commissioned; it fires on nothing.
CFO/Growth/Product-Analyst are advisors (consulted at contract time),
not reviewers. **Model tiering** (CPO ruling 2026-06-12, pinned in each agent's
`model:` frontmatter): `scope-auditor` and the six specialists all on
**sonnet**. The pin is a floor — on a guard path (`.claude/hooks/**`,
`.claude/agents/**`, `.claude/commands/**`, `.claude/settings.json`,
`.claude/review_routing.json`, `.mcp.json`, `.cursor/mcp.json`,
`.github/workflows/**`, `.gitlab-ci.yml`) every **specialist** routing requires is spawned on **opus**
(a procedural override, not hook-enforced), because guard bypasses are the costliest
misses. `scope-auditor` is exempt from that OPUS PROMOTION — it sits in `always`, so
"every reviewer" would promote it on every governance commit. It ran on **haiku**
until 2026-08-06; the exemption withheld the most expensive tier and was being read
as justifying the cheapest, on the reviewer that sees every diff. That means
`cto-reviewer` on
all nine, **plus `platform-reviewer` on exactly three**, `.claude/hooks/**`,
`.github/workflows/**` and `.gitlab-ci.yml`: the CTO rules on authority, Platform on the implementation,
and the G3 bypasses were fail-open and test-coverage findings, which are Platform's.
Platform is absent from the other six by design — a brief is a prompt, not
machinery, so its verdict there would be a rubber stamp. **Check this against the
rows before restating it**: the split's own review caught it wrong twice, once as
prose over-claiming and once as rows widened to match the prose at a cost nobody
had approved.

### Project skill — `.claude/skills/validate-local/` (committed)

`validate-local` runs the same gates CI runs, locally, before pushing — the
direct antidote to fix-after-CI churn. Tier 1 (fast/offline), Tier 2 (needs
BigQuery auth: dbt parse + sqlfluff), Tier 3 (full build/DQ — CI-only).

### Global hooks — `~/.claude/settings.json` → `~/.claude/hooks/*.py` (NOT in repo)

Project-agnostic. Apply to **every** project on this machine. Canonical copies
live in `docs/portable_guardrails/` so they can be version-controlled and copied
elsewhere.

> ⚠️ **NONE OF THESE IS INSTALLED. Every row below runs nowhere** (verified 2026-07-22:
> `~/.claude/settings.json` has no `hooks` key at all, and there is no other user-level settings
> file). This table described intent and was read as fact for months — the same failure that let
> `handover_in.py` be documented as "unavoidable" while nothing invoked it. The scripts are real
> and live in `docs/portable_guardrails/`; installing them is a manual step nobody has taken.
> **Treat this table as a shopping list, not an inventory.** If a behaviour here matters, move
> the hook into `.claude/hooks/` and wire it in `.claude/settings.json`, where it is protected,
> reviewed and committed — which is what was done for `handover_in.py`.

| Hook | Event / trigger | Would do (NOT RUNNING) |
|---|---|---|
| `plan_implement_gate.py` | PostToolUse ExitPlanMode | Right after a plan is approved: re-read the standards governing the files about to change; name the layer/module each change belongs in; hold to scope; plan to validate before pushing. |
| `pre_push_gate.py` | PreToolUse Bash | Before a real `git push`: run local validation first (avoid the CI round trip); confirm the push targets a feature branch, not main/master. |
| ~~`handover_in.py`~~ | SessionStart | **Moved into the project set (2026-07-22) — see above.** It was listed here as a global hook and was running nowhere: the user-level settings carry no `hooks` key at all. The copy that runs here is `.claude/hooks/handover_in.py`, on a protected path. ⚠️ The copy still in `docs/portable_guardrails/hooks/` is the **PRE-fix** one: it carries the characters-versus-bytes truncation bug and has no truncation warning at all. Port the project copy before reusing it elsewhere. |
| `handover_plan_gate.py` | PreToolUse Edit/Write/MultiEdit | On the first code edit of a session where a handover exists, requires restating the locked spec and getting user approval before writing code. Fires once per session; skips edits to the handover file. The safety net that puts the user back in the loop before divergence becomes work. |
| `handover_out.py` | PreToolUse Bash | On a real `git push`, reminds to update `.claude/active_work.md` to reflect the new status. Keeps the handover current for the next session. (Reminder, not a hard block — a crying-wolf push block would get ignored.) |

⚠️ **`handover_in.py` NOW OVERLAPS, and following the install procedure below would double-fire
it.** `docs/portable_guardrails/settings.snippet.json` still registers `handover_in.py` under
`SessionStart`, and the install steps below say to copy every portable hook into `~/.claude/hooks/`
and merge that snippet. Do that on this machine and every session start injects the handover
TWICE, roughly 26 KB, one copy being the pre-fix one with the character-versus-byte truncation bug.
**When installing the portable set here, drop the `SessionStart` entry from the snippet.** The
other four have no project twin and cannot collide. (The snippet is not edited here: it belongs to
the portable archive, which this task deliberately leaves alone. Fixing it is a separate unit.)

### The enforced handover — `.claude/active_work.md`

Continuity across chats is enforced, not hoped for. Each project keeps a single
**`.claude/active_work.md`** — a short, authoritative handover: current task, the
locked spec (or link), status (done / in-progress / next concrete action), and an
explicit **do-NOT** list. It is the *only* thing a fresh chat is guaranteed to read
(injected by `handover_in.py`). The loop:

- **Read-in (hard):** `.claude/hooks/handover_in.py` injects it at SessionStart. *"Unavoidable"
  was wrong for months*: nothing was wired to SessionStart anywhere, so the injection never
  happened and this document said otherwise. Wired in the project settings on 2026-07-22.
- **Size is a hard constraint, not a style note.** The injection is capped at 16,000 **characters**
  (the unit matters: the hook once read characters and decided truncation from the file's size in
  bytes, so a handover under one cap and over the other was injected whole and labelled cut). The
  handover reached 112,233 and would have been delivered 14% deep and cut off in silence. It is
  now under the cap, the hook announces truncation when it happens, and the file's own header
  states the budget. Keep it current state only; history belongs in git.
- ⚠️ **Plan-back and write-out DO NOT RUN.** `handover_plan_gate.py` (restate-and-approve before
  the first code edit) and `handover_out.py` (a push reminder to update the handover) are both in
  the not-installed global set above. So the loop has ONE enforced leg, the read-in, and two that
  exist only as intentions. The plan-back's job is covered in practice by plan mode plus the
  contract gate; the write-out's is not covered by anything, which is why the handover goes stale
  unless someone remembers.

This exists because a fresh chat once re-scoped a fully-specified task (it read the
issue title + memory and built the wrong thing). Auto-loaded memory was not enough —
the handover must be a single focused file, pushed in, with the user as the gate.

---

## Carrying the portable set to a new project

The **portable** hooks are generic. There are five of them and, as of 2026-07-22, **none is
installed on this machine** — see the warning on the global table above. To set them up on a
machine or for a new project (dropping `SessionStart` from the snippet if the project already
ships its own `handover_in.py`, as this one now does):

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
  (the repo copy is canonical) — **except `handover_in.py`, which is no longer portable.** It was
  promoted into `.claude/hooks/` on 2026-07-22 and fixed there; the archive copy is deliberately
  the older one and is NOT kept in sync. Port from the project copy, not the archive.
