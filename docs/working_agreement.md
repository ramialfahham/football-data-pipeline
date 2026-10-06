# Working agreement — agent behaviour

This document holds the rules every AI agent (Claude, Cursor or any other) follows in this
repository. The rules are non-negotiable. Read this document before doing anything.

`docs/agent_guardrails.md` lists the hooks that enforce these rules and what each hook does.

---

## 1. Permission to act — the five-step protocol

Every unit of work runs **Explore → Plan → Confirm → Implement → Verify**. Explore, Plan,
Implement and Verify each have a machine gate. Confirm is the human checkpoint.

| Step | What it is | Gate |
|---|---|---|
| **Explore** | Read-only investigation that traces the system before any proposal. | The impact-map gate (§2) denies the first structural edit until the contract carries a non-placeholder `impact_map`. |
| **Plan** | The task contract: objective, scope, decisions, `done_when`. | The contract gate (§2) denies every edit without a contract and every edit outside `scope_paths`. |
| **Confirm** | **WAIT for the user's explicit go before implementing.** | Plan mode (below). |
| **Implement** | The edits, inside `scope_paths` only. | The scope and protected-path gates (§2). |
| **Verify** | `done_when`, the review cycle and the commit gate. | The review cycle and `git_discipline.py` (§2). |

- Do **not** edit files, run terminal commands or start implementation without permission.
  Permission is a clear request for that action, such as "implement this", "run it" or "commit
  and push". An explicit go-ahead after the agent presented options is permission too.
- Exploring tradeoffs, thinking out loud, asking "what should I do?" or venting frustration is
  **not** permission to change the repo or run tools. Answer only, with options, risks and a
  recommendation, then wait.
- When in doubt, ask **one** short clarifying question instead of acting.

**Confirm gate — plan mode.** For any task that will touch files, enter plan mode at the Plan
step (`EnterPlanMode`) and present the plan-back. The harness then blocks every edit until the
user approves the exit (`ExitPlanMode`). That approval is the Confirm. Plan mode is read-only, so
it covers Explore and Plan. An explicit go from the user for the specific change on the table is
also the Confirm, and plan mode is then unnecessary.

**Sources.** `CLAUDE.md` ("Which source answers which question") states which source answers
which question; this document does not restate it. Memory answers none of them.

**The requirement is a GitLab issue, and the plan is part of it.**

- Every major task gets one issue in the shape of `.gitlab/issue_templates/Task.md`.
- Its *What exactly* is a checklist, and each line is checkable without reading code. Its *How*
  is the plan, in at most 7 lines. Exploration detail sits below a fold.
- The builder writes the issue from the conversation.
- The plan shown for approval is the issue's text, not a second document. The CPO approves those
  lines and nothing else.
- The task contract's `acceptance_criteria` copies the checklist verbatim. Blinded reviewers
  cannot read GitLab.
- A question the issue does not answer is asked. The answer is edited into the issue, never
  appended to a log.
- A typo or a refactor with no requirement needs no issue. Its MR head says "No behaviour change".

---

## 2. The task contract, the review cycle and the commit gate

### Task contract

Every unit of work begins with a **task contract** at `.claude/task/contract.md`. The builder
writes it before touching any file and commits it with the branch, so the MR shows it.
`.claude/task/TEMPLATE.md` holds its format.

| Field | What it holds |
|---|---|
| `objective`, `refs` | What the task builds and why, tied to the issue. |
| `scope_paths` | The file allowlist. The contract gate denies every edit outside it. |
| `decisions_taken` | What the contract pre-approves, naming the approval each item rests on. |
| `decisions_reserved` | Every known CPO-class question (§10). Each is escalated blinded (§11), never decided. |
| `acceptance_criteria` | Testable statements of what the built page must do. Required when the diff touches `site_v2/src/`, the user-facing surface. |
| `impact_map` | The evidenced end-to-end blast-radius map. Required before the first edit on the structural surface. |
| `protected_override` | Where and when the CPO approved a protected-path edit, never a quote. Required before any protected-path edit. |
| `done_when` | Mechanical verification steps. |
| `amendments` | Scope extensions, each recording the CPO authority. |

**`decisions_reserved` and published artifacts.** An `Artifact` publish needs a contract whose
`decisions_reserved` holds real content. What a page shows is a §10 decision. It is reserved and
escalated, never answered by drawing it.

**`acceptance_criteria`.**

- The builder drafts them, and the CPO approves them **before any code**.
- After approval they are locked. Only the CPO may change them.
- The commit gate denies a commit without them.
- The commit gate also denies a commit until `.claude/task/acceptance_evidence.md` demonstrates
  every criterion under a `criteria_demonstrated:` marker. The evidence is read from the built
  output.

**`impact_map`.**

- The structural surface is `ingestion/**`, `dbt_project/models/**`, `scripts/export_*.py`,
  `site/**`, `site_v2/**` and every protected path.
- The map names every writer of the table or model, and the downstream lineage to marts and
  consumption.
- It also names the CI layer rules that apply, the shared-warehouse deploy order and the blast
  radius. The blast radius is the marts and numbers that change, or "none" with the RAW or leaf
  evidence.
- Lineage from `dbt ls --select <model>+` or the dbt MCP is pasted as evidence, never asserted
  from memory.
- A trivial, leaf or cosmetic change uses a one-line evidenced short form.
- The gate checks that the map is present. The routed reviewer judges its honesty. A dishonest
  "trivial" short form is a FAIL (Appendix A6).

**Consult before building** (a norm, not a gate). On a structural change, gather the domain
knowledge first: a reviewer role, a document or a data check. Do not discover it in review.

**`amendments`.**

- The builder writes every amendment on a clean tree.
- A contract change is reviewed and bound by the review hash. It rides in the reviewed commit,
  never in a later artifact-only commit.
- An amendment after the code commit needs a re-stage and a new review cycle. Otherwise the review
  hash breaks and CI rejects the MR.

If anything could silently shrink scope or affect something not listed, stop and ask. An
extension of the contract without recorded CPO authority is drift.

### Protected paths

The protected paths are `.claude/hooks/**`, `.claude/agents/**`, `.claude/commands/**`,
`.claude/settings.json`, `.claude/review_routing.json`, `.mcp.json`, `.cursor/mcp.json`,
`.github/workflows/**` and `.gitlab-ci.yml`. A guard path is a protected path.

- A protected path is editable only in a dedicated, CPO-approved governance task.
- That task's contract carries both `protected_override` and a non-placeholder `impact_map`.
- The override answers "may you". The map answers "do you know what breaks".

### File changes and history

- File changes go through the Edit and Write tools only. Never write a repo file with shell
  redirection, `sed -i`, `tee` or a script heredoc.
- `git commit --amend`, `--no-verify`, `-n` and repointing `core.hooksPath` are forbidden. History
  stays append-only and hook-verified.
- A decision is recorded by the thing it changes, never by a log (§11).

### Review cycle

Every substantive commit passes four serialized steps. The commit gate enforces them.

| Step | What happens |
|---|---|
| 1. Code Lock | The builder declares the implementation complete and stages everything with `git add`. No further edits happen in this cycle. |
| 2. Blinding | The required reviewers are spawned cold and judge the cumulative branch diff. |
| 3. Cross-Examination | Each reviewer returns an adversarial verdict. |
| 4. Lock | The verdicts, the review hash and the round count go into `.claude/task/review.md`. |

**Blinding.**

- `.claude/review_routing.json` names the required reviewers for the staged paths:
  `scope-auditor` always, plus the path-routed specialists.
- Each reviewer gets read-only tools and no builder context.
- Each reviewer judges the cumulative branch diff from the base branch, never the staged
  increment alone. The diff is in `.claude/task/review_input.patch`.
- `git_discipline.py --review-patch` generates that patch. Nobody writes it by hand.
- The patch leaves out the task notes in `.claude/task/` that `review_exclude_paths` lists.
- `contract.md` stays in the patch. It carries the scope, the acceptance criteria and the approval
  behind a `protected_override`.
- A reviewer never approves a §10 decision.

**Reviewer models.**

- Each reviewer definition pins its model, and every one pins **sonnet**. The pinned model is a
  floor.
- When the staged diff touches a guard path, every specialist that routing requires for it is
  spawned at **opus**.
- `scope-auditor` is exempt from the opus promotion. It never runs below the **sonnet** floor.
  Its tier is a recurring cost and a CPO decision (§10).
- For the guard paths, that means `cto-reviewer` on all nine, plus `platform-reviewer` on exactly
  three of them: `.claude/hooks/**`, `.github/workflows/**` and `.gitlab-ci.yml`.
- The CTO rules on authority. Platform reviews the implementation.
- `platform-reviewer` is deliberately absent from the other six, `.claude/agents/**` above all. A
  reviewer brief is a prompt, not machinery.
- The orchestrator applies this rule at spawn time. No hook enforces it.
- Never state this rule in prose without checking it against the routing rows. Fix a mismatch on
  whichever side is wrong, which is almost always the prose.
- Widening the rows adds an opus specialist. That is a recurring cost and a CPO decision.
- `tests/test_governance_doc_parity.py` checks this prose against the routing rows.

**Cross-Examination.**

- A FAIL names a defect: the file, the line and what goes wrong. No concrete failure, no FAIL.
- A PASS may find nothing. It lists what the reviewer examined under `risks_checked:`, with at
  least one entry. "Checked X against Y, no defect" is a complete entry.
- Praise is banned. A finding made up to justify a pass is banned too.
- A reviewer keeps a critical attitude and is allowed to approve.
- A re-review after the first round is a delta review. The reviewer gets only what changed since
  its own last PASS.
- The delta reviewer judges that change plus its own prior findings, not the whole diff again. It
  FAILs when the change is too large for its last PASS to stand.

**Lock.**

- `.claude/task/review.md` holds the verdicts, the review hash and a `rounds:` count. Its format
  is `.claude/task/REVIEW_TEMPLATE.md`.
- The review hash is the SHA-256 that `python .claude/hooks/git_discipline.py --staged-hash`
  prints. It covers the cumulative branch diff: the code and `contract.md`.
- The hash leaves out the bookkeeping artifacts that `hash_exclude_paths` lists. They include the
  two evidence artifacts, `acceptance_evidence.md` and `rendered_page_evidence.md`.
- CI recomputes the hash from `git diff base...HEAD`.
- `contract.md` is hashed and is never artifact-exempt. Every contract change goes through review.
- The round count is capped at 3. Past the cap, the builder stops and brings the open findings to
  the CPO.
- To continue on the CPO's say-so, `review.md` records `rounds_cap_override: <reason>`.

### Commit gate

`git_discipline.py` denies `git commit` when any of these is true:

- `review.md` is missing.
- Its hash does not match the live hash, or the live hash cannot be computed.
- Any verdict is FAIL.
- An ESCALATE has no recorded `CPO ANSWER:` in its own section.
- A required reviewer has no verdict.
- A PASS has nothing under `risks_checked:`.
- The `rounds:` line is missing or is not a positive integer.
- `rounds:` exceeds the cap of 3 without a `rounds_cap_override:`.
- The diff touches `site_v2/src/`, and the acceptance criteria are missing or not all
  demonstrated.

A commit whose staged paths all match the routing file's `artifact_only` patterns is exempt. A
commit that touches `contract.md` is never exempt.

The commit form:

- Only `git add` followed by a plain `git commit` is allowed.
- The allowed commit flags are `-m`/`--message`, `-F`/`--file`, `-q`/`--quiet`, `-v`/`--verbose`,
  `-S`/`--gpg-sign` and `-s`/`--signoff`.
- Every other flag and every pathspec is denied. They can stage content at commit time, after the
  hash check.
- A git global option between `git` and `commit` is denied. The only allowed spelling is exactly
  `git commit`.
- `git commit` is the sole command in its shell call. A chained sibling such as
  `git add x && git commit` could restage content after the hash check.

CI re-checks the artifacts on every MR with `scripts/check_task_artifacts.py`.

---

## 3. Branches — always

Every change goes on a **new branch**. Never commit directly to `main`. Never push to `main`. Open
an MR and wait for CI and explicit user approval before merging.

**Process:**

1. `git checkout -b feature/name`, never with `gitlab/main` as the tracking target.
2. Do the work and commit.
3. `git push gitlab feature/name`, with the explicit remote branch name.
4. Open an MR, then wait for CI and user approval.

A `gitlab/main` tracking target sends pushes directly to `main`. Never rely on implicit tracking.

**Never run `glab mr merge`.** Merging is the user's action, not the agent's. The agent's job ends
when the MR is open and CI is green. Never run `glab mr merge` or its `glab mr accept` alias for
any reason, `--auto-merge` included. The one exception is the user typing "merge it", or an equivalent, in
the same message.

### 3a. Branch consolidation — check before branching

Before creating a new branch, ask: **is this work logically part of something already in
flight?**

Run `glab mr list` and answer two questions:

1. **Is the work a hard dependency?** The open MR cannot pass CI or be correct without it.
2. **Does separating it buy anything?** Independent reviewability, an earlier merge path, or a
   meaningfully smaller MR.

| Both questions | Correct action |
|---|---|
| Hard dependency AND separation buys nothing | Commit to the existing branch. Do not open a second MR. |
| Hard dependency BUT can stand alone and merge first | New branch, merge it first, rebase the dependent MR on main. |
| Not a dependency — genuinely independent work | New branch. |

"New ticket = new branch" is correct only when the work is genuinely independent, or can stand
alone with a clear review benefit. Reflexive branching for every adjacent fix creates
merge-ordering complexity and splits coherent work for no gain.

---

## 4. Quality is non-negotiable

- **No hacky solutions.** If the clean solution takes longer, say so and agree on the timeline. Do
  not ship a workaround and call it done.
- **No unnecessary complexity.** Do not introduce abstractions, layers, helpers or patterns that
  the current task does not require. Three clear lines beat a premature abstraction every time.
- **No scope creep.** Implement exactly what the user agreed. Flag an adjacent fix separately. Do not
  fold it into the current change without agreement.
- **No half-finished implementations.** If a task cannot be completed cleanly, say so before
  starting, not halfway through.

---

## 5. Do not work against the user

- Never change any of these to make a run finish faster or to unblock quickly:
  - `.env`;
  - the ingest profile;
  - the default season-window constant, `DEFAULT_SEASON_WINDOW_YEARS`;
  - a competition's `history_seasons`;
  - fanout or cost caps.
- The only exception is explicit confirmation in the same thread.
- Never silently narrow scope. An example is dropping to a single season while implying that the
  full configured band is satisfied.
- If API daily limits require multiple days or scheduled runs, say so clearly and point at
  `docs/operations_guide.md`.

---

## 6. Layer contract — dbt

Each dbt layer has a strict purpose. A violation is a quality defect, not a style preference.
`dbt_project/docs/layering.md` holds the full layer rules.

| Layer | Purpose |
|-------|---------|
| `1_staging` | Raw cleanup only: renaming, casting, unnesting, flattening. One model per raw source table. No business logic. No cross-source unions. |
| `2_base` | First business logic: deduplication, UNION ALL across sources, entity alignment. Preparation for core. |
| `3_core` | System of record: canonical dimensions and facts. Surrogate keys, grain enforcement. |
| `4_intermediate` | Complex transforms and feature engineering that do not belong in a consumption model. |
| `5_marts` | Consumption layer: flattened, denormalised, optimised for the app and analysis. |

If logic does not belong in the current layer, move it to the correct one. Do not bend the rules
because it is convenient.

---

## 7. Data quality is non-negotiable

The user cannot verify numbers by hand. Every metric and every pipeline output must have automated
tests. "It looks right" is not acceptable. Tests must catch issues before they reach the UI.

---

## 8. Competition-agnostic by default

`league_code` is the competition discriminator on everything. Never hardcode `D1` or any other
competition identifier in business logic. Every model, metric and UI component must work for any
value of `league_code` without modification.

---

## 9. Communication style

- Plain language, technically accurate.
- Explanations, issues, MR heads and documents follow ISO 24495-1 (plain language): the reader finds, understands and can use what they need.
- Every term, table row and rule in a document follows ISO/IEC 11179-4. It states what the thing is, stands alone, and leaves out rationale, history and procedure.
- Sentences follow ASD-STE100: one word, one meaning; one topic per sentence; active voice; at most 20 words in a procedure and 25 in a description.
- No filler, no analogies, no motivational text, no emoji unless asked.
- Use backticks for file, function, and column names.
- Proposals proportional to the request — do not over-engineer simple tasks.
- When something goes wrong, say what happened, why, and what the correct approach is. Do not bury it.

---

## 10. Decision rights — who decides what

The agent never decides the following. Each is a CPO decision, escalated per §11, every time,
however obvious the answer seems.

| CPO-only decision class | Examples |
|---|---|
| Product/UX content, composition, ordering | page modules, metric row order, what a screen shows |
| Metric definitions, labels, formats | `metric_catalogue` rows, display strings |
| Anything permanent once published | URL formats, slug spelling, public identifiers |
| User-visible naming and wording | labels, names, copy, badge text |
| NEW mechanisms of any kind | warehouse object classes (UDFs), lifecycle hooks, libraries, services, workflow steps |
| Rule reinterpretation or extension | applying a written rule to a domain it did not explicitly cover |
| Changing shipped numbers | anything a published page displays |
| Cost, schedule, scope | API budget, history depth, run cadence, widening a task |
| Core document text | every edit to `north_star.md`, `site_architecture.md`, `content_architecture.md`, `ui_design_brief.md`, `working_agreement.md`, `agent_guardrails.md`, `metrics_context_model.md`: the exact text, approved before the edit |

**Agent-executable:** implementation inside a written contract, and mechanical work whose every
judgment a contract document already codifies. The contract documents are layering, engineering
standards, the metric catalogue and the task contract.

**The meta-rule:** when a new case does not clearly match a written rule, the classification
itself is a CPO decision. An analogy to an existing rule is not a licence (Appendix A3).

---

## 11. Blinded escalation protocol

**Premise check.** Before escalating, the agent runs a mandatory `<premise_check>` in its
thinking. It lists the assumptions under the escalation, validates each against the written rules
and drops every invalid premise. The CPO never sees an escalation built on a false premise.

**Two paths.** The escalation presents **at least two distinct, conflicting paths**. For each
path it states what the path implies, what it costs and what becomes hard later. The statement is
honest enough that the CPO could pick the path the agent did not recommend.

**End with a recommendation, and say why**. Two forms of anchoring are forbidden: shading the
alternatives to make the recommendation look inevitable, and guessing what the CPO wants to hear.
The recommendation is the agent's reasoning made visible so that it can be attacked. It is not a
nudge.

**Where the answer goes.** A decision is recorded by the thing it changes, and nowhere else.

| The decision changes… | The record is… |
|---|---|
| **code** | the MR. The CPO merges it, and the merge is the approval. |
| **a rule**: how we work, what a screen shows, what a metric means | the document that owns that rule, **edited in the same MR**. The new text replaces the old text, never appended to it. |
| **a requirement** for work not yet built | that work's GitLab issue, edited in place |
| **a locked file** (a protected path) | the contract's `protected_override` and the MR head's `Locked files` line. They name the approval, where and when, and never quote it. The merge is the approval. |
| nothing durable | not a decision. Nothing is written. |

**The MR head is the CPO's check.**

- The commit message body carries `Closes #N` and the `Locked files:` line that names the
  approval.
- The post-commit hook opens the MR with `glab mr create --fill`. Both lines reach the MR
  description that way and stay in `git log`.
- Right after, the builder sets the MR description to the full shape of
  `.gitlab/merge_request_templates/Default.md` (`glab mr update <n> --description …`).
- The head holds the issue's checklist, ticked, with one link per tick, and the same
  `Locked files:` line. Everything else sits below a fold.
- The merge is the one act the builder cannot perform, so the merge is the approval. Nothing is
  recorded until the CPO merges.
- No record quotes the CPO.
- The CPO reads the head before merging and refuses a long one.

---

## Appendix A — Historical anti-patterns

Each row is a failure class that reviewers and escalations hunt for and cross-reference, with the
form it takes in this project. A newly caught failure class gets a new row. This appendix is
binding.

| Id | Failure class | What it looks like |
|---|---|---|
| A1 | Metric creation or redefinition without catalogue approval | Player metrics invented outside the catalogue, such as per-90 rates, `goal_conversion` or a player `shot_accuracy` |
| A2 | Product decision fabricated and presented as agreed | A home-page composition written into merged documents as settled, with no discussion behind it |
| A3 | Rule over-extension, and a new mechanism without approval | URL formatting classed as a "transformation" and pulled into dbt. Persistent UDFs and an `on-run-start` lifecycle hook added unilaterally to satisfy a linter. |
| A4 | Consumption-side shortcut instead of source-of-truth architecture | The v2 export planned through `mart_matchday_insights`, the MVP's presentation pivot |
| A5 | Logic or transformation in the frontend, a consumption-layer violation | W/D/L results, player-to-team affiliation or rankings derived in the Python export |
| A6 | Spot-fix without the blast-radius map; coverage cut as a data-quality fix; assertion before measurement | A data or grain bug fixed one layer at a time, without the end-to-end map. Less ingestion proposed as the fix because older data is messier. A claim made before counting the offending rows in RAW. The `impact_map` rule (§2) prevents this class. |
