# Task contract — handover: the ingest silent-failure cluster is closed, cost is next

> Written on a clean tree before any file was touched. Branch
> `chore/handover-ingest-cluster-complete` from `main` at `c3e23f3`. No protected path in scope, so
> no `protected_override`. No structural path in scope, so no `impact_map`. No `site_v2/src/` path,
> so no `acceptance_criteria`.

objective: >
  Bring `.claude/active_work.md` up to date so a cold chat continues with zero re-investigation. It
  is currently four PRs stale: it states that nothing is in flight and that #896, #897 and #898 are
  open and unstarted. All three are merged, and cause 3 of #898 is merged on top. A fresh session
  reading it today would redo work that is already live.

  It also carries one item that this session RESOLVED and must not be left as open: transfers
  healing was recorded as INFERRED and NOT OBSERVED. It is now observed.

refs: >
  #897 merged (`d2b5789`), #896 merged (`0a4f636`), #898 merged (`e7758a6`), cause 3 merged
  (`c3e23f3`). Filed this session and still open: #900 (stale blueprint cost model), #904 (contract
  claims are unverified). Cost programme is #547, with #895, #892 and #890 as its ranked items.

scope_paths:
  - .claude/active_work.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/escalations.log

decisions_taken: >
  None. This records state that already exists and decides nothing. Every ruling it references is
  already in `escalations.log` or on a GitHub issue with its authority.

  `.claude/active_work.md` is in `scope_paths` from the start, declared here on a clean tree rather
  than amended in later. VERIFIABLE PRECEDENT rather than an assertion: the merged #899 handover
  contract listed exactly this path first in its own `scope_paths`. Check it with
  `git show 36b5f98:.claude/task/contract.md`. The failure recorded in `escalations.log` was adding
  this path MID-TASK to a CODE branch while citing a rule that did not exist, which is a different
  thing from declaring it up front on a dedicated handover branch.

  ⚠ REVIEWER NOTE, because this already produced one false FAIL on this task.
  `.claude/active_work.md` is listed in `review_exclude_paths` in `.claude/review_routing.json`, so
  `git_discipline.py --review-patch` OMITS it from `review_input.patch` BY DESIGN. Its absence from
  the patch is NOT evidence that it was not modified. It is modified: 62 insertions, 38 deletions
  per `git diff --cached --stat`. READ IT FROM THE WORKING TREE. A previous scope audit of the #899
  handover did exactly that and recorded the reasoning.

  THRESHOLD DECLARATIONS. NEW MECHANISM: none. RECURRING COST: none, and this is the one case where
  "none" is safe without a figure, because the diff contains no executable line.

decisions_reserved:
  - The cost work itself (#547) is NOT started here. This task only points at it.
  - #904's lint is filed, not built.
  - Nothing about tomorrow's nightly is asserted. No paced run has happened yet, so the handover
    must record the fixes as merged but UNVERIFIED in production, not as proven.

done_when:
  - `.claude/active_work.md` is under 16,000 CHARACTERS (it is 12,602 before this edit).
  - It names, for a cold reader: current main, that the ingest cluster is closed, that cost is next
    with its ranked list, and that no production run has yet exercised any of the four fixes.
  - The transfers-healing item is stated as OBSERVED with its evidence, not as unverified.
  - Every claim that was corrected this session appears in corrected form only, with no "this used
    to say" narration, per the standing correction-replaces rule.
  - The commit touches only artifact paths. It still requires a scope audit, because `contract.md`
    is never artifact-exempt (F10/#409).

amendments: (none)
