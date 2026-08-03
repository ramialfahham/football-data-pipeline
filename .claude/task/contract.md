# Task contract — handover after the cost work (#547 PR1, #890)

> Written on a clean tree before any file was touched. Branch `chore/handover-cost-work` from
> `main` at `bb61a51`. No protected path in scope, so no `protected_override`. No structural path
> in scope, so no `impact_map`. No `site_v2/src/` path in scope, so no `acceptance_criteria`.

objective: >
  Bring the handover to current state after four merges: #846 and #886 (the featured season and its
  DQ guard), #547 PR1 (base models become tables, plus the cost-measurement script and the policy
  guard) and #890 (the ingestion read stops scanning all partitions).

  This is its own commit on purpose. It was attempted inside #890's branch by widening that
  contract's `scope_paths` to admit `.claude/active_work.md`, and `scope-auditor` failed it because
  the authority cited was a rule I had named rather than a recorded ruling. The correct answer was
  not a better citation: a commit touching only `.claude/task/**` and `.claude/active_work.md` is
  already exempt from the review cycle, so the handover never needed to ride in a code branch.

refs: >
  #846, #886, #547, #890. Bookkeeping only — no issue is closed or opened by this, and no decision
  is taken.

scope_paths:
  - .claude/active_work.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/escalations.log

decisions_taken: >
  None. This records state that already exists; every ruling it mentions is already in
  `escalations.log` with its authority.

  THRESHOLD DECLARATIONS. NEW MECHANISM: none. RECURRING COST: none — no query, model, workflow or
  scheduled run is touched. This is the one case where "none" is safe to write without a figure,
  because the diff contains no executable line.

decisions_reserved:
  - none: the handover states what was decided and by whom, and decides nothing itself. Where a
    question is open (#845 with #882, and #892) it is recorded as open rather than resolved.

done_when:
  - `.claude/active_work.md` is under the 16,000 CHARACTER limit, measured in characters and not
    with `wc -c`, which counts bytes and over-reports on this file.
  - It names what a fresh chat needs first: current main, what is in flight, and that #892 is the
    remaining half of the cost work.
  - The commit touches only artifact paths, so the commit gate's artifact exemption applies and no
    review cycle is required.

amendments: (none)
