# Review — chore/handover-refresh-621 — 2026-07-02

> G3 Lock artifact. Bookkeeping-only handover refresh: brings .claude/active_work.md current after #621
> (#530(b) merged, main @ 46719fb). Records the Stats-percentile track pick, the PARKED Player Stats
> wireframe (stash@{0} on docs/391-player-stats-percentile-spec) + a recovery/rework callout, #620/#621 in
> RECENT PRs, and the percentile display contract pointer. Required set (routing): scope-auditor only —
> the diff touches .claude/active_work.md (artifact) + .claude/task/contract.md (hashed). No specialist route.
>
> Round 1 (hash 75ff1894) FAIL — the rework callout claimed items "all CPO-settled" while item 4 (naked-%)
> was an open question; stash-recovery lacked a conflict guard.
> Round 2 (hash 75ff1894, active_work-only edits) FAIL — the median word "middle" was tagged [SETTLED]/(CPO
> pick) but the memory (feedback_percentile_display_phrasing.md) marks it "CPO-to-confirm" — over-asserted.
> Round 3 (hash ba740469, THIS lock) — per-item STATUS tags: item 1 [STRUCTURE SETTLED] + median word
> [WORD PROVISIONAL, CPO-to-confirm]; items 2–3 [SETTLED]; item 4 [OPEN, CPO/football-analytics escalation];
> contract decisions_taken reworded to "records decisions + faithfully marks open/provisional items";
> stash-conflict guard added. scope-auditor PASS.

diff_sha256: ba740469210c227e132b4234a40b92a3c9ea4bcbbd346dfac40ab767ba067bfe

## scope-auditor
VERDICT: PASS
risks_checked:
- Stash-recovery fragility — if `git stash pop` conflicts on the parked wireframe branch, the callout
  directs re-creation from the rework list (a prose 4-item summary, not an executable diff). Verified the
  list is detailed enough (status tags, metric names, explicit rules) to re-create the spec, and a clear
  priority rule (rework list = source of truth on conflict) is stated. Real but documented + guarded. Held.
- Provisional-word binding drift — the median word "middle" is marked [WORD PROVISIONAL] with explicit
  "CPO-to-confirm" language matching the memory exactly; the handover no longer asserts it as decided. The
  soft-vs-hard ambiguity (from "Let's try it") is inherited from the source, not created here, and correctly
  flagged for the CPO to restate at rework. Naked-% (item 4) correctly OPEN. Bookkeeping-only; scope =
  .claude/active_work.md + .claude/task/**; no §10 decision made/hidden. Held.

## escalations
(none here) — the two OPEN/provisional items (the median word "middle" = CPO-to-confirm; the naked-%
denominators for save%/duels%/dribbles% = CPO/football-analytics call) are RECORDED in the handover as
to-be-resolved at the wireframe rework (their own task + review cycle), not decided in this bookkeeping refresh.
