# Review — chore/retire-obsolete-scripts — 2026-06-13

> Issues #423/#424 (audit F14/F15): delete two obsolete, unreferenced scripts.
> Pure removal. Required reviewers for scripts/: scope-auditor + cto-reviewer.

diff_sha256: 63f0506e43c5051cd0fd9d8f70ff9d8e5a8ee9bf00112cd235f8b3815846545f

## scope-auditor
VERDICT: PASS
risks_checked:
- Live caller detection: grep across .github/workflows/, scripts/, and docs/ found
  zero references to either `scaffold_domestic_league_staging.py` or
  `add_footer_i18n_keys.py` outside the audit record and this task's artifacts. The
  scaffolder's purpose (per-competition staging) is impossible under the zero-file
  rule; the footer script is a complete one-time migration. No live caller persists.
- Scope boundary + §10: the diff deletes exactly the two named scripts and nothing
  else (`.claude/active_work.md` not touched in this commit); deleting CPO-approved
  dead code is not a §10 act — no metric/naming/mechanism/cost change is smuggled in.

## cto-reviewer
VERDICT: PASS
risks_checked:
- Live CI invocation: grepped `.github/workflows/` for both script names — zero
  matches; neither script is a step in any workflow.
- Module import from other code: grepped all `.py` for `from scripts.scaffold*` /
  `from scripts.add_footer*` — zero matches; both are standalone CLIs, never imported.
- Diff completeness: both entries are `deleted file mode 100644` with full content
  removed; no partial deletion or dangling stub. Neither file is a guard path. A
  doc note: the audit doc names both (historical record, not a run instruction) — no
  doc tells anyone to run them, so no stale-doc blocker.

## escalations
(none — both reviewers PASS.)
