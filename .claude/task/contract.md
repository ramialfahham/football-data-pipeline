# Task contract — handover refresh (end of session 2026-06-25)

> Governance G2/G3 contract. Written on a clean tree BEFORE any edit.
> Artifact/doc task — `.claude/active_work.md` is NOT auto-editable, so it is named in scope_paths.

objective: >
  Refresh `.claude/active_work.md` to the current truth: #573 (slim CI) and #574 (#500 PR1, team
  metric consolidation) are MERGED; record the cost diagnosis, the no-macro/compose decision, the
  pending orphaned-table cleanup, and PR2 (player formula-dedup only) as the next unit — so a cold
  chat tomorrow continues frictionlessly.
refs: #500; end-of-session handover.

scope_paths:
  - .claude/active_work.md

decisions_taken: >
  Documentation only — no product/code/§10 decisions. Records decisions already made this session
  (no-macro/compose per CPO; entity-first naming; player models do NOT merge).

decisions_reserved:
  - None new. (The orphaned-table drop is a CPO action — bq rm is deny-listed; commands are recorded
    for the CPO to run. Formalising an explicit Explore->Plan->Confirm->Implement->Verify protocol in
    the guard docs is a CPO decision flagged for tomorrow.)

done_when:
  - .claude/active_work.md leads with: #573 + #574 MERGED; PR2 (player, formula-dedup only) as the
    next build; the do-NOTs (CPO merges; don't drop _season; don't merge the player season models;
    Bash only; contract-first); the byte-identical verification recipe; the pending bq rm cleanup.
  - Routes to scope-auditor only (active_work.md is in no routing path); PASS; commit is artifact-only
    (active_work.md + contract.md) — note contract.md makes it NON-exempt, so scope-auditor must run.

amendments: (none)
