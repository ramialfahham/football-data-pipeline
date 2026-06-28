# Review — chore/handover-2026-06-29-sot-merged — refresh active_work.md handover

> G3 Lock artifact. Reviewer spawned cold (blinded) on the staged diff (`.claude/task/review_input.patch`).
> Required set (routing): always → scope-auditor only — the diff touches `.claude/active_work.md` +
> `.claude/task/contract.md` (no code path). Doc-only handover refresh after PR #598 (TEAM
> deserved-vs-actual / SoT rank-space gap) merged; contract.md is `artifact_only_never` (hashed), so
> review is required (not exempt).

diff_sha256: 7267ea805d96bfa7d487aada54ceaf81f90eadd84a1292da9b6424628143e365

## scope-auditor
VERDICT: PASS
risks_checked:
- Git-state honesty: the handover asserts main GREEN at #598 (cc1bfd0), #598 MERGED, the 4 new
  catalogue rows + the new int_team_season__deserved_vs_actual model live, data-build pass. A cold
  chat verifies by `git checkout main && git pull` + the commit hash; the claims are sourced to the
  MERGED #598 contract + memory [[project-team-metric-rank-correlation-sweep]]. Verified consistent
  with the actual merged state (cc1bfd0 carries the model + 4 rows; data-build passed 3m45s).
- §10 record-vs-decide: the handover RECORDS already-made decisions (the SoT design, the 4 rows, gap
  display = neutral, intermediate-only scope, the formula-vs-availability ruling, the nullability-clause
  house style) citing their sources, and reserves the next task to the CPO ("none auto-granted"). The
  'Null when…' description-prose clause is faithful to the pre-existing catalogue convention
  (shot_accuracy/save_ratio) and the CPO's in-session approval recorded in #598's review.md — a record,
  not a new metric/format decision. No NEW §10 decision asserted.
findings:
- none

## escalations
(none) — doc-only handover refresh; records sourced decisions (MERGED #598 contract + memory) and reserves the next task to the CPO.
