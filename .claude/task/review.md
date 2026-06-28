# Review — chore/handover-2026-06-28-post596 — refresh active_work.md handover

> G3 Lock artifact. Reviewer spawned cold (blinded) on the staged diff (`.claude/task/review_input.patch`).
> Required set (routing): always → scope-auditor only — the diff touches `.claude/active_work.md` +
> `.claude/task/contract.md` (no code path → analytics-engineer/cto/etc. dormant). Doc-only handover
> refresh; contract.md is `artifact_only_never` (hashed), so review is required (not exempt).
> First round FAILED on missing authority citations; fixed by citing each decision's source (merged
> #596 contract, memory) + framing unbuilt SoT work as candidates. This is the re-review.

diff_sha256: 69d902b3af234d75b08cccfeb67c8b7fe555a936611f97d84f28a23efb2de164

## scope-auditor
VERDICT: PASS
risks_checked:
- The "#596 MERGED / main is GREEN" assertion is not evidenced with git metadata in the diff. Checked:
  the current tree's seed carries the formula columns (base_relation/numerator_expr/denominator_expr),
  the formula-vs-availability ruling is already in #596's decisions_taken, and memory records the CPO
  ruling dated 2026-06-28 — all consistent with a same-session merge. Handled well: the claim is
  falsifiable by the next chat in seconds (`git checkout main && git pull` either shows the formalized
  seed or not), and no code is shipped on the assumption — only the handover's next-step direction.
- The SoT metric candidate names (`sot_difference`, `sot_against`) could be misread as CPO-approved,
  collapsing the "design method settled" vs "metric rows not yet approved" boundary. Checked: the
  contract decisions_taken states "No NEW … metric / naming decision here"; the SoT build entry requires
  "football-analytics + CPO sign-off BEFORE building"; decisions_reserved reserves the next-task pick to
  the CPO; the candidates header says "none auto-granted". Handled well — the boundary is explicit and
  the names are framed as candidates, not approvals.

## escalations
(none) — no NEW §10 decision is asserted; the handover records sourced decisions (merged #596 contract +
memory) and reserves the next task to the CPO.
