# Task contract — handover: next is #150, then #109 step 3; the mirror items are closed

objective: >
  Bring `.claude/active_work.md` to the state after the CPO's ruling of 2026-09-18, "#150 first":
  the next unit of work is #150 (competition page, Matchdays tab) in a fresh chat, plan mode; #109
  step 3 follows it, still gated on the 2026-09-19 nightly being green; the README badge (!206) and
  the token note (!207) are merged, the runbook rewrite is #154. Under 16,000 characters.

refs: >
  CPO in chat, 2026-09-18: "merged, #150 first", answering the recommendation "#150 first; the
  nightly check is a two-minute read at the start of whichever chat comes first, and step 3 can
  follow the builds". !206, !207 merged 2026-09-18; #154 filed 2026-09-18.

scope_paths:
  - .claude/active_work.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch

decisions_taken: >
  None. The handover's "next" pointer and the mirror paragraph rewritten to what he decided and
  merged; the tracker snapshot is not regenerated because the previous handover commit regenerated
  it minutes ago and the only tracker change since is #154, which the snapshot at the next session
  end will carry.

decisions_reserved:
  - none.

done_when:
  - `.claude/active_work.md` names #150 as next and #109 step 3 after it; the badge and token items are no longer listed as open; `len()` under 16,000.

amendments: (none)
