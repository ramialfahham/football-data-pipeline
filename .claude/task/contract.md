# Task contract — the handover header names the commit before its own merge

objective: >
  `.claude/active_work.md`'s header says **main `b29f2e0`** and "!154 through !161". Both were true
  when the file was written and stale the moment it merged: main is now `6f296f5` and the range runs
  to `!162`. A header that names the wrong commit is the one line a fresh session cannot sanity-check
  the rest of the file against. Fix it, and make the class not recur.

refs: >
  The CPO, verbatim, this session: *"fix the handover header"*.
  ⚠ Structural, not a slip. The header records the state at WRITE time; the file is READ after its
  own MR merges, so the SHA it names is always one commit behind by construction. This has now been
  wrong on three consecutive handover MRs.

scope_paths:
  - .claude/task/contract.md
  - .claude/task/acceptance_evidence.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/escalations.log
  - .claude/active_work.md

impact_map: >
  writers: none. One header line in one tracked document.
  layer_rules: not applicable.
  downstream: read by a fresh session at start and by `handover_in.py` (16,000-CHARACTER cap,
  Python `len()`).
  deploy_order: none.
  blast_radius: two lines. The risk is a session trusting a stale SHA and concluding the rest of the
  file is stale too — or worse, that work it can see on main is unrecorded.

acceptance_criteria:
  - The header no longer pins a SHA that will be wrong on merge. What it states must still be TRUE
    after this branch merges, which is the test the previous three headers failed.
  - The MR range is current, and stated so it does not need editing for the merge that carries it.
  - Everything else in the file is untouched — this is a two-line change, not another rewrite.
  - Under 16,000 characters.

decisions_taken: >
  ⭐ **DROP THE SHA, KEEP WHAT IS CHECKABLE.** A commit hash in a file that merges as a commit is
  self-invalidating: the header can only ever name its own parent. It bought nothing a reader uses —
  `git log -1` answers "where is main" instantly and correctly, which the file cannot. What a reader
  actually needs from the header is the date, that the tree is clean, whether anything is open, and
  which platform. Those survive their own merge.
  ⛔ **NOT SOLVED BY REMEMBERING TO UPDATE IT.** Three handover MRs in one day each carried a header
  that was accurate when written and wrong when read. A rule that requires the author to predict the
  commit they are about to create is the wrong shape; removing the field removes the class.
  ⚠ The MR range keeps its upper bound as the last MERGED one and says so, rather than naming the MR
  in flight — a range that includes its own MR is a claim about the future.