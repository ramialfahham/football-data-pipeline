# Review — chore/handover-drop-untracked-candidates — 2026-07-04

> G3 Lock artifact. Bookkeeping/handover correction — removes the brainstormed, UNTRACKED "further
> player-season models" ideas (multi-season trend / per-position YoY / milestones) from `.claude/active_work.md`
> at all three occurrences (header NEXT clause, FIRST STEPS step 3, Phase C backlog entry), keeping only the
> genuinely tracked backlog (#530(b), #510, #484). Those ideas were an Explore-agent brainstorm offered as
> declined options in a "which YoY-extension" AskUserQuestion (CPO picked "enrich existing YoY block" = #648);
> the prior refresh (#649) over-formalized them as "remaining candidates". CPO ruled this session: DROP entirely.
> Plan mode skipped per the CPO handover carve-out (2026-06-30); the contract + review + gate still run.
> Required set (routing): scope-auditor only (always) — no `dbt_project/**`, `scripts/**`, CI, ingestion, or
> wireframe/i18n path is touched.

diff_sha256: 209b5f665c597e9eb7057616d68778ff4f06d48262d7206687e17cd0be3a3a29

## scope-auditor
VERDICT: PASS
risks_checked:
- **Stray-reference survival + completeness.** Verified all three named occurrences (header NEXT clause,
  FIRST STEPS step 3, Phase C backlog entry) are removed in the diff, and grep found no surviving reference to
  the untracked ideas ("multi-season trend" / "per-position YoY" / "milestones" / "further player-season
  models") anywhere in the live handover prose — only in the diff/artifact files. The real tracked backlog
  (#530(b), #510, #484) remains intact as the only candidates; replacement language explicitly states no new
  player-season surface is tracked (a brand-new one needs a display spec + CPO go first), preventing
  re-introduction.
- **Scope + no collateral damage.** Only `.claude/active_work.md` + `.claude/task/contract.md` are staged —
  within scope_paths; no `dbt_project/**`, `scripts/**`, `ingestion/**`, or `site*/` change smuggled in. All
  other handover facts left intact and correct: main-GREEN pointer 1966d4d, the #648/#645/#638 records, the
  Phase D shelve note, the player-streaks skip, the history-backfill finding, #391 un-paused, and the full
  RECENT PRs section. §10 hygiene sound: the diff executes a CPO decision already ruled this session
  (drop-vs-relabel → drop), inventing nothing new.

## escalations
- None. No open escalations; no ESCALATE verdict raised.
