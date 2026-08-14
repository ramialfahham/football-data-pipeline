# Task contract — handover write-out after #62 step 1

objective: >
  `.claude/active_work.md` is stale. It says "ONE MR OPEN: `!27`" when `!27`, `!37`, `!39` and
  `!40` have all merged and NOTHING is in flight, and its CURRENT section describes `!27` as the
  work in progress. `handover_in.py` injects this file into every new session at SessionStart, so
  a stale handover is the one document a fresh chat is guaranteed to read and act on.

  Bookkeeping only: no code, no model, no test, no shipped number.

refs: >
  Merged this session: #63 (!35), #33 items 9/14/15, #65 (!37), #57 (!33), #367 (!27),
  #33 completeness-gate (!39), #62 step 1 (!40). main is `10fa570`.
  New issues filed this session: #69 (countries as an entity), #70 (scan-budget guard, from the
  other worktree), plus #64/#67/#68 earlier.

scope_paths:
  - .claude/active_work.md
  - .claude/task/contract.md
  - .claude/task/escalations.log
  - .claude/task/review.md
  - .claude/task/review_input.patch

decisions_taken: >
  1. ⚠ **CORRECTED — I ARGUED FOR NO REVIEW ROUND AND THE GATE WAS RIGHT TO REFUSE IT.** The first
     version of this item said "NO REVIEW ROUND IS RUN", reasoning that the routing yields only the
     always-on scope-auditor, that the diff is a status document with no code or guard in it, and
     that paying adversarial-review price for prose is what `feedback_review_cost_discipline`
     warns against. The commit gate rejected `rounds: 0` — it counts review rounds and requires at
     least one — so the round ran.
     The gate was right and the argument was wrong: cost discipline is about not over-reviewing,
     not about opting out of the mechanism. **It also earned its keep immediately** — scope-auditor
     FAILED round 1 on this very item, because the superseded "no round is run" text was still
     standing as though true, which is precisely the "a correction REPLACES, never accumulates"
     rule the handover being written here states.
     The mechanical verification still applies and is recorded in `review.md`: under the character
     cap, unique NEXT numbering, no conflict markers, every MR/issue number checked against `glab`
     rather than recalled.

  2. The CURRENT section is REPLACED, not appended to. A handover accumulates until it lies; the
     rule is that a correction replaces. What goes out: `!27` as in-flight, and the four MRs that
     have since merged.

  3. The rebase-tax paragraph STAYS even though nothing is in flight, because it is the most
     expensive recurring lesson of the session — four rebases, every one conflicting in exactly
     the same paperwork files — and the next branch will hit it again.

done_when:
  - `active_work.md` names main `10fa570`, states nothing is in flight, and lists #62's remaining
    steps as the next work.
  - Under 16,000 CHARACTERS measured with Python `len()`, NEXT numbering unique, zero conflict
    markers.
  - Every MR and issue number in it verified against `glab mr list` / `glab issue list`.

amendments: []
