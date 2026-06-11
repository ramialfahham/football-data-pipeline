# Active work — handover

> The single handover contract. A fresh chat is given this file (via the `handover_in`
> SessionStart hook). Continue from here; do not re-scope or infer from issue titles or
> memory. Keep it current (status + next action + do-NOTs). Update it before you finish.

_Last updated: 2026-06-11 (governance build). **The website blueprint (#391) is PAUSED
by CPO order.** Current program: the agent-governance system (approved plan:
`C:\Users\Rami\.claude\plans\fuzzy-launching-meadow.md` — READ IT FIRST). G1 MERGED
(#401). **G2 open as PR #402 — and its gates are LIVE in the repo settings**: every
edit now requires a task contract at `.claude/task/contract.md` (template:
`.claude/task/TEMPLATE.md`); out-of-scope edits and shell writes are DENIED; the stop
gate blocks turn-end on contract mismatch. Next = G3 (role reviewers + commit gate)._

## Why the pivot (do not re-litigate)
The CPO repeatedly caught agent drift by watching live (wrong-layer logic, unilateral
CPO-class decisions, rule over-extension — see working_agreement.md Appendix A). He
will not keep supervising. Until the governance machinery lands, NO blueprint or
feature work proceeds.

## The governance program (approved 2026-06-11, two Gemini review rounds + CPO edits)
1. **G1 — MERGED (#401)**: working_agreement.md §10 Decision rights (CPO-only
   classes + meta-rule: unclear classification is itself a CPO decision), §11
   Blinded escalation (premise_check; ≥2 conflicting paths; NO recommendation),
   Appendix A Historical anti-patterns (A1–A5). CLAUDE.md pointer; hook-message
   pointers.
2. **G2 — OPEN, PR #402, gates LIVE**: `task_contract_gate.py` (edit + shell + post-
   Bash check), `stop_gate.py`, git_discipline flag denies
   (`--amend`/`--no-verify`/`-n`/hooksPath), TEMPLATE.md, working_agreement §2
   machine-gated, 27 hook tests in tests/test_governance_hooks.py. Live-fire
   verified: out-of-contract Write denied, shell redirect denied, quoted ">" not
   false-positived. NOTE FOR EVERY FUTURE TASK: write the contract FIRST (clean
   tree), or all edits are denied.
3. **G3**: refresh role briefs (analytics_engineer.md is pre-refactor stale!) →
   read-only reviewer subagents `.claude/agents/analytics-engineer-reviewer.md` +
   `scope-auditor.md` (praise banned; default FAIL; PASS requires ≥2 real risks
   found, else FAIL + forced CPO escalation; cross-reference Appendix A) → serialized
   4-step cycle (Code Lock → Blinding → Cross-Examination → SHA-256 Lock in
   `.claude/task/review.md`) → commit gate in git_discipline.py (no review artifact /
   hash mismatch / FAIL verdict / unanswered ESCALATE → commit denied) → CI backstop
   `scripts/check_task_artifacts.py` + PR template governance block.
4. **G4**: retroactive audit — scope DISCUSSED WITH CPO at kickoff (he said "wider,
   maybe history"; plan proposes current-state-first + history-for-provenance).
5. **Pilot**: rework the parked marts branch under the full workflow.

## Parked state (do not touch until the pilot)
- Branch `data/marts-gap15-16-19`: GAP-15/16/19 mart work, built & verified, stashed
  as `stash@{0}` ("parked: marts-gap15-16-19 pilot work"). Contains the slug/UDF work
  that triggered the governance pivot — it gets REWORKED under the new workflow.
- Two CPO rulings pending, to be escalated BLINDED during the pilot: (1) where slugs
  are produced (frontend slug-map vs warehouse), (2) slug spelling (transliteration
  vs ASCII-strip). Do NOT pre-decide either.
- Blueprint resume-state (when CPO un-pauses): PR 3 = screens 04–07; slim export PR;
  GAP-18 tournament windows before WC 2026; GAP-17 ruling pending.

## Do NOT
- **No blueprint/feature/data work while the governance program is incomplete.**
- **Never decide CPO-class questions** (working_agreement §10); escalate blinded
  (§11) — no recommendations in escalations.
- Do not compute anything in the frontend/export (layering.md §Consumption layer).
- Do not touch the live MVP; do not change shipped numbers (GAP-17 parked).
- File edits via Edit/Write tools only — never shell redirection/heredocs (A-pattern;
  G2 enforces).
- Honor the task contract at `.claude/task/contract.md`: no edits outside
  scope_paths; amendments only on a clean tree, naming the CPO authority.
- Branch from main; never commit to main; the post-commit hook auto-pushes + opens
  PRs.

## Environment notes
- dbt/sqlfluff from project `.venv`. BQ is a SHARED single environment (CI rebuilds
  from whichever branch built last — redeploy before BQ-based verification).
- sqlfluff 4.1.0 parse-depth cliff ≈ 7 nested calls (relevant to the parked slug
  work; the UDF approach in the stash was the unapproved workaround — see A3).
