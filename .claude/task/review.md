# Review — chore/handover-2026-06-25 — handover refresh (end of session)

> G3 Lock artifact. Reviewer spawned cold (blinded) on the staged diff
> (`.claude/task/review_input.patch`). Required set for the staged paths (.claude/active_work.md +
> .claude/task/contract.md): scope-auditor only (no routing path matches; the commit carries
> contract.md so it is NOT artifact-exempt). Docs/handover-only — no model/seed/script/CI/guard change.

diff_sha256: 67c83e1c51080ef17386728d22218b58e402c5e79793aef67cf8c78a4905e9e4

## scope-auditor
VERDICT: PASS
risks_checked:
- Scope: the diff touches ONLY .claude/active_work.md + .claude/task/contract.md (both in scope_paths);
  no code/config/guard path smuggled in.
- §10 decision rights: the handover records only ALREADY-MADE decisions (slim CI #573 + PR1 #574, each
  approved in its own review; the no-macro/compose + entity-first naming CPO rulings; the player models
  do-not-merge finding) and explicitly RESERVES future CPO items (the _season drop / PR-d §10s; the
  orphaned-table drop as a CPO action; formalising the protocol). No new §10 decision is invented.
- Honesty / consistency: the byte-identical claim carries a specific count (0/12,537 x 48); the cost
  diagnosis is measured (INFORMATION_SCHEMA.JOBS_BY_PROJECT); the fct_transfer correction is
  self-annotated with the commit hash; the do-NOTs (CPO merges, don't drop _season yet, Bash only,
  contract-first) are preserved; the older #500 PR-a/b/c/d framing is marked superseded.

## escalations
(none)
