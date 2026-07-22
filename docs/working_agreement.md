# Working agreement — agent behaviour

This document governs how any AI agent (Claude, Cursor, or other) operates in this repo. It is non-negotiable. Read it before doing anything.

---

## 1. Permission to act — the five-step protocol

Every unit of work runs **Explore → Plan → Confirm → Implement → Verify**. Four of the
five are machine-gated; **Confirm is the human checkpoint** and is the subject of this
section. The asymmetry is the point — three of the steps below gate on an *artifact* a
hook can read, but "did the user say go?" lives in chat, so Confirm needs its own gate.

| Step | What it is | Gate |
|------|-----------|------|
| **Explore** | read-only investigation; trace the system before proposing | impact-map gate (§2) — first structural edit denied until the contract carries the evidenced blast-radius map |
| **Plan** | the task contract — objective, scope, decisions, done_when | contract gate (§2) — no contract, no edits; out-of-scope path denied |
| **Confirm** | **WAIT for the user's explicit go before implementing** | THIS section + plan mode (below) |
| **Implement** | the edits, inside `scope_paths` only | scope + protected-path gates (§2) |
| **Verify** | done_when + the 4-step review cycle + the commit gate | review cycle + `git_discipline.py` |

- Do **not** edit files, run terminal commands, or start implementation unless the user clearly asked for that action ("implement this", "run it", "commit and push") or replied with an explicit go-ahead after options were presented.
- Exploring tradeoffs, thinking out loud, asking "what should I do?", or venting frustration are **not** permission to change the repo or run tools. Answer only — options, risks, recommendation — then wait.
- When in doubt, ask **one** short clarifying question instead of acting.

**Confirm gate — plan mode (the mechanism).** For any task that will touch files, enter
**plan mode** at the Plan step (`EnterPlanMode`): present the plan-back, then the harness
blocks every edit until the user approves the exit (`ExitPlanMode`). That approval *is*
the Confirm — a real human checkpoint, not a remembered courtesy. Plan mode is read-only,
so it fits Explore + Plan exactly. If the user has already given an explicit go for the
specific change on the table, that go is the Confirm and plan mode is unnecessary. (A
self-attested `cpo_go` contract token enforced by the impact-map gate was considered and
**held in reserve** — adopt it only if plan mode proves insufficient; a new gate must earn
its place over the simplest thing that works.)

---

## 2. Before any non-trivial change — the task contract (machine-gated)

Every unit of work begins with a **task contract** at `.claude/task/contract.md`
(template: `.claude/task/TEMPLATE.md`), written BEFORE any file is touched and
committed with the branch so it is PR-visible:

- **objective + refs** — what and why, tied to the issue/gap/plan
- **scope_paths** — the surgical file allowlist; the contract gate
  (`.claude/hooks/task_contract_gate.py`) DENIES any edit outside it
- **decisions_taken** — what the contract pre-approves, quoting the CPO ruling
- **decisions_reserved** — known CPO-class questions (§10); each is escalated
  blinded (§11), never decided
- **impact_map** — REQUIRED when `scope_paths` touches the **structural surface**
  (`ingestion/**`, `dbt_project/models/**`, `scripts/export_*.py`, `site*/`, **and
  every protected path** — see below; added 2026-07-22): the
  end-to-end blast-radius map produced BEFORE the first structural edit — every
  writer of the table/model, the downstream lineage to marts/consumption (from
  `dbt ls --select <model>+` or the dbt MCP, **pasted as evidence, not asserted
  from memory**), the CI layer rules that apply, the shared-warehouse deploy
  ordering, and the blast radius (which marts/numbers change, or "none" with the
  RAW/leaf evidence). The gate denies the first structural edit until it is
  present; the routed reviewer judges its honesty — a dishonest "trivial"
  short-form is a FAIL (Appendix A6). This makes the trace-first habit a
  precondition, not guidance. Trivial/leaf/cosmetic changes use a one-line
  evidenced short-form. The gate checks PRESENCE; correctness is the reviewer's.
- **done_when** — mechanical verification steps
- **amendments** — scope extensions, written on a CLEAN tree, each recording the
  CPO authority. A contract change is reviewed and hash-bound (F10/F11, #409): it
  rides INTO the reviewed commit, never a separate later artifact-only commit. If
  you must amend after the code is committed, re-stage and re-run the review cycle —
  a post-commit contract change breaks the review hash and CI rejects it.

Mechanics enforced by hooks (see `docs/agent_guardrails.md`):
- No contract → repo edits denied. Out-of-scope path → denied.
- **Structural surface** (`ingestion/**`, `dbt_project/models/**`,
  `scripts/export_*.py`, `site*/`, **and every protected path below**) → the
  first Edit/Write is denied until the contract carries a non-placeholder
  `impact_map` (§2 above / Appendix A6). Enforced on the shell write path too,
  not only on Edit/Write.
- **An `Artifact` publish is denied without a contract carrying a real
  `decisions_reserved`** (2026-07-22). Design was the only surface with no gate
  at all: three player-page mocks were produced and rejected in a single day
  without a contract, a routed reviewer or a commit gate ever seeing them.
  "What does this page show" is a §10 decision, reserved and escalated, never
  answered by drawing it. **Honest limit:** this is keyed on the `Artifact` tool
  name, not on the act of designing. Writing an HTML mock to a scratchpad with
  `Write` still touches nothing, because every path-keyed check returns early
  outside the repo. Publishing is gated; drafting is not.
- **Protected paths** (`.claude/hooks/`, `.claude/agents/`,
  `.claude/commands/`, `.claude/settings.json`, `.claude/review_routing.json`,
  `.mcp.json`, `.cursor/mcp.json`, `.github/workflows/`) are never editable
  except in a dedicated CPO-approved governance task whose contract carries
  `protected_override` **and a non-placeholder `impact_map`** — both, since
  2026-07-22. They are two different questions: the override answers "may you",
  the map answers "do you know what breaks". Until that date only the override
  was required, so editing a guard demanded *less* evidence than a cosmetic
  label change on a leaf mart, while a guard's blast radius is every future task
  in the repo. The reviewer definitions and routing are protected so
  the builder can never weaken its own adversary inside an ordinary task (CPO
  ruling, G3 escalation 2026-06-12); `.claude/commands/` is protected because
  custom slash commands can embed shell, so a command file is the same
  high-stakes class as a hook (CPO ruling 2026-06-14); `.mcp.json` /
  `.cursor/mcp.json` (and any `mcpServers` block in `.claude/settings.json`)
  are protected because an MCP-server config auto-launches a command every
  session — the same command-class, so an agent can never self-grant an MCP
  server in an ordinary task (CPO ruling 2026-06-18).
- **File changes go through the Edit/Write tools only** — shell redirection,
  `sed -i`, `tee`, and script heredocs are denied for repo files; a post-command
  check and the turn-end stop gate force reversion of anything that slips
  through.
- `git commit --amend`, `--no-verify`/`-n`, and `core.hooksPath` repointing are
  denied — history stays append-only and hook-verified.
- Escalations are appended to `.claude/task/escalations.log` (committed).

**The review cycle (governance G3)** — every substantive commit passes the
serialized four steps; the commit gate enforces them mechanically:

1. **Code Lock** — implementation declared complete; everything staged via
   `git add`; no further edits this cycle.
2. **Blinding** — the reviewers required by `.claude/review_routing.json` for
   the staged paths (the Scope-Auditor always, plus the path-routed
   specialists) are spawned cold: read-only tools, no builder context, judging
   the CUMULATIVE branch diff (written to `.claude/task/review_input.patch`).
   Reviewer models are pinned in each agent definition for economy:
   `scope-auditor` runs on **haiku**, the five specialists on **sonnet**. The
   pinned model is a floor — when the staged diff touches a guard path
   (`.claude/hooks/**`, `.claude/agents/**`, `.claude/commands/**`,
   `.claude/settings.json`, `.claude/review_routing.json`,
   `.github/workflows/**`), the orchestrator
   spawns `cto-reviewer` with its model overridden to **opus**, because guard
   bypasses are the highest-stakes findings (the G3 commit-gate bypasses were
   caught only at that depth). This is a procedural rule the orchestrator
   applies at spawn time, not a hook-enforced one.
3. **Cross-Examination** — adversarial verdicts under the no-free-pass rule: a
   PASS must name at least two real risks checked; a reviewer that cannot find
   two must FAIL/ESCALATE; praise is banned; §10 decisions are never approved
   by a reviewer.
4. **Lock** — verdicts + the SHA-256 of the staged diff
   (`python .claude/hooks/git_discipline.py --staged-hash`) written to
   `.claude/task/review.md` (format: `.claude/task/REVIEW_TEMPLATE.md`). The hash
   covers the substantive diff — code **and** `contract.md` — EXCLUDING the
   bookkeeping artifacts (`hash_exclude_paths` in review_routing.json), so CI can
   recompute it from `git diff base...HEAD` and bind the review to the PR's actual
   code (F11/#409). `contract.md` is never artifact-exempt, so a contract change
   always goes through review (F10/#409).

`git commit` is DENIED when: review.md is missing, its hash does not match the
live staged diff (code + contract, bookkeeping excluded), any verdict is FAIL, an ESCALATE lacks a recorded
`CPO ANSWER:` in its own section, a required reviewer has no verdict, or a
PASS lacks its two risks. **Only `git add` + plain `git commit` is allowed** —
commit flags are allowlisted (`-m`/`--message`, `-F`/`--file`, `-q`, `-v`,
`-S`/`--gpg-sign`, `-s`/`--signoff`); every other flag and any positional
pathspec is denied, because the self-staging forms (`-a`/`--all`/`-am`,
`-i`/`--include`, `-o`/`--only`, `-p`/`--interactive` — including bundled
spellings like `-qam` and prefix abbreviations like `--inc`) stage content at
commit time, after the hash was computed. Git global options between `git`
and `commit` (`git -p commit`, `git --git-dir x commit`) are denied for the
same reason — the only allowed spelling is exactly `git commit`. The commit
must also be the SOLE command in its shell call: a chained sibling
(`git add x && git commit -m …`) could restage content after the hash was
verified. Commits touching only governance artifacts
(`.claude/task/**`, `.claude/active_work.md`) are exempt. CI re-checks the
artifacts on every PR (`scripts/check_task_artifacts.py`); the PR template
surfaces the trail.

If anything could silently shrink scope or affect something not listed, stop and
ask — extending the contract without recorded CPO authority is drift by
definition.

---

## 3. Branches — always

Every change goes on a **new branch**. Never commit directly to `main`. Never push to `main`. Create a PR and wait for CI and explicit user approval before merging.

**Correct process:**
1. `git checkout -b feature/name` — never with `origin/main` as the tracking target (causes pushes to go directly to main)
2. Do the work and commit
3. `git push origin feature/name` — explicit remote branch name, never rely on implicit tracking
4. Open a PR; wait for CI and user approval

**Never run `gh pr merge`** — merging is the user's action, not the agent's. The agent's job ends when the PR is open and CI is green. Running `gh pr merge` for any reason, including `--auto`, is not permitted unless the user explicitly types "merge it" or equivalent in the same message.

### 3a. Branch consolidation — check before branching

Before creating a new branch, ask: **is this work logically part of something already in flight?**

Run `gh pr list --state open` and consider two questions:

1. **Is the work a hard dependency?** — the open PR cannot pass CI or be correct without it.
2. **Does separating it buy anything?** — independent reviewability, an earlier merge path, or a meaningfully smaller PR.

| Both questions | Correct action |
|---|---|
| Hard dependency AND separation buys nothing | Commit to the existing branch. Do not open a second PR. |
| Hard dependency BUT can stand alone and merge first | New branch, merge it first, rebase the dependent PR on main. |
| Not a dependency — genuinely independent work | New branch. |

"New ticket = new branch" is only correct when the work is genuinely independent or can stand alone with clear review benefit. Reflexively branching for every adjacent fix creates merge-ordering complexity and splits coherent work for no gain.

---

## 4. Quality is non-negotiable

- **No hacky solutions.** If the clean solution takes longer, say so and agree on the timeline — do not ship a workaround and call it done.
- **No unnecessary complexity.** Do not introduce abstractions, layers, helpers, or patterns that are not required by the current task. Three clear lines beat a premature abstraction every time.
- **No scope creep.** Implement exactly what was agreed. If you spot something adjacent worth fixing, flag it separately — do not fold it into the current change without agreement.
- **No half-finished implementations.** If a task cannot be completed cleanly, say so before starting, not halfway through.

---

## 5. Do not work against the user

- Never change `.env`, the ingest profile, the default season-window constant (`DEFAULT_SEASON_WINDOW_YEARS`) or a competition's `history_seasons`, or fanout/cost caps to "make a run finish faster" or "unblock quickly" without explicit confirmation in the same thread.
- Never silently narrow scope (e.g. dropping to a single season while implying the full configured band is satisfied).
- If API daily limits require multiple days or scheduled runs, say so clearly and point at `docs/operations_guide.md`.

---

## 6. Layer contract — dbt

Each dbt layer has a strict purpose. Violating it is a quality defect, not a style preference.

| Layer | Purpose |
|-------|---------|
| `1_staging` | Raw cleanup only: renaming, casting, unnesting, flattening. One model per raw source table. No business logic. No cross-source unions. |
| `2_base` | First business logic: deduplication, UNION ALL across sources, entity alignment. Preparation for core. |
| `3_core` | System of record: canonical dimensions and facts. Surrogate keys, grain enforcement. |
| `4_intermediate` | Complex transforms and feature engineering that do not belong in a consumption model. |
| `5_marts` | Consumption layer: flattened, denormalised, optimised for the app and analysis. |

If logic does not belong in the current layer, move it to the correct one — do not bend the rules because it is convenient.

---

## 7. Data quality is non-negotiable

The user cannot manually verify numbers. Every metric and pipeline output must be covered by automated tests. "It looks right" is not acceptable. Tests must catch issues before they reach the UI.

---

## 8. Competition-agnostic by default

`league_code` is the partition key on everything. Never hardcode `D1` or any other competition identifier in business logic. Every model, metric, and UI component must work for any value of `league_code` without modification.

---

## 9. Communication style

- Plain language, technically accurate.
- No filler, no analogies, no motivational text, no emoji unless asked.
- Use backticks for file, function, and column names.
- Proposals proportional to the request — do not over-engineer simple tasks.
- When something goes wrong, say what happened, why, and what the correct approach is. Do not bury it.

---

## 10. Decision rights — who decides what

The agent never decides the following. Each is a CPO decision, escalated per §11 — every time, regardless of how obvious the answer seems.

| CPO-only decision class | Examples |
|---|---|
| Product/UX content, composition, ordering | page modules, metric row order, what a screen shows |
| Metric definitions, labels, formats | `metric_catalogue` rows (existing rule), display strings |
| Anything permanent once published | URL formats, slug spelling, public identifiers |
| User-visible naming and wording | labels, names, copy, badge text |
| NEW mechanisms of any kind | warehouse object classes (UDFs), lifecycle hooks, libraries, services, workflow steps |
| Rule reinterpretation or extension | applying a written rule to a domain it did not explicitly cover |
| Changing shipped numbers | anything the live MVP or published pages display |
| Cost, schedule, scope | API budget, history depth, run cadence, widening a task |

**Agent-executable:** implementation inside a written contract; mechanical work whose every judgment is already codified in a contract document (layering, engineering standards, metric catalogue, the task contract).

**The meta-rule:** when a new case does not clearly match a written rule, the classification itself is a CPO decision. "It's analogous to X" is not a license — that analogy produced the slug/UDF incident (Appendix A3).

## 11. Blinded escalation protocol

Before escalating, the agent runs a mandatory `<premise_check>` in its thinking: list the assumptions underlying the escalation, validate each against the written rules, and drop invalid premises — the CPO never sees an escalation built on a false premise.

The escalation itself presents **at least two distinct, conflicting paths**. For each path state what it implies, what it costs, and what becomes hard later, honestly enough that the CPO could pick the one the agent did not recommend.

**End with a recommendation, and say why.** (Corrected 2026-07-22. This section used to ban one — "no preferred option, no recommendation" — and that rule was both stale and inconsistently followed: `escalations.log` holds 9 escalations that withheld a recommendation and 8 that gave one. The CPO wants the recommendation: leading with a bolded call and its reasoning is faster to judge than a neutral menu, and a menu with no view is often an undigested choice handed over rather than a decision genuinely reserved.) Anchoring is still forbidden in one specific sense: never shade the alternatives to make the recommendation look inevitable, and never guess what the CPO wants to hear. The recommendation is the agent's reasoning made visible so it can be attacked, not a nudge.

Every escalation is appended to `.claude/task/escalations.log` (committed with the branch) once the task-contract machinery exists.

---

## Appendix A — Historical anti-patterns (live reference)

Concrete past failures of this project. Reviewers and escalations cross-reference this list; each entry names the failure class to hunt for. Extend it whenever a new class is caught — this appendix is law, not history.

| # | Incident | Failure class |
|---|---|---|
| A1 | Invented player metrics in #325 (per-90 rates, goal_conversion, player shot_accuracy) | Metric creation/redefinition without catalogue approval |
| A2 | Home-page composition written into two merged docs as settled when it was never discussed | Product decision fabricated and presented as agreed |
| A3 | Slug/UDF incident: URL formatting classified as "transformation" and pulled into dbt; persistent UDFs + an `on-run-start` lifecycle hook introduced unilaterally to satisfy a linter | Rule over-extension + new mechanism without approval |
| A4 | v2 export initially planned through `mart_matchday_insights` (the MVP's presentation pivot) | Consumption-side shortcut instead of source-of-truth architecture |
| A5 | W/D/L results, player→team affiliation, and rankings derived in the Python export | Logic/transformation in the frontend (consumption-layer violation) |
| A6 | Diagnosis drift across #514/#527/#536: spot-fixing a data/grain bug one layer at a time without the end-to-end map; framing "older data is messier" → proposing to ingest LESS as the "fix"; asserting before counting the offending rows in RAW. Each caught only one layer downstream, costing many round-trips | Spot-fix without the blast-radius map / coverage-cut as a DQ fix / assert-before-measure (the `impact_map` rule, §2, exists to prevent this) |
