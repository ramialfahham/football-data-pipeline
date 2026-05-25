# Working agreement — agent behaviour

This document governs how any AI agent (Claude, Cursor, or other) operates in this repo. It is non-negotiable. Read it before doing anything.

---

## 1. Permission to act

- Do **not** edit files, run terminal commands, or start implementation unless the user clearly asked for that action ("implement this", "run it", "commit and push") or replied with an explicit go-ahead after options were presented.
- Exploring tradeoffs, asking "what should I do?", or venting frustration are **not** permission to change the repo or run tools. Answer only — options, risks, recommendation — then wait.
- When in doubt, ask **one** short clarifying question instead of acting.

---

## 2. Before any non-trivial change

State a short block first:
- **Intent**: what you are about to do
- **Files / systems touched**: every file, table, workflow, or external service affected
- **Definition of done**: what "finished" looks like and how it will be verified

If anything could silently shrink scope or affect something not listed, stop and ask.

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

- Never change `.env`, the ingest profile, the season-window constant (`V1_SEASON_WINDOW_YEARS`), or fanout/cost caps to "make a run finish faster" or "unblock quickly" without explicit confirmation in the same thread.
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
