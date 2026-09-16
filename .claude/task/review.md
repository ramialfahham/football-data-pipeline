# Review — docs/scale-follows-value — 2026-09-16

diff_sha256: 5a078962c436b2bd3c360feff9ec917c05772b30adfc872a7659c186bdbd44b5

rounds: 1

## scope-auditor
VERDICT: PASS
risks_checked:
- Scope: the three changed files (`docs/north_star.md`, `CLAUDE.md`, `.claude/task/contract.md`)
  are in `scope_paths`; nothing else staged.
- §10: a rule written into the document that owns it, with the CPO's wording and his confirmation
  recorded in `decisions_taken`; no decision taken beyond that wording.
- Appendix A: no stale claim arguing against a feature from its page or row count survives in
  `docs/north_star.md`, `CLAUDE.md` or `docs/site_architecture.md`; the only mention of the
  2026-09-16 failure is the new text naming what is forbidden.
- Impact map: not owed; no ingestion, dbt, export, site or protected path in the diff.
- `decisions_reserved` honoured: the build's out-of-memory defect and the page-count check are
  left to the Matchdays build issue.

## escalations
(none)
