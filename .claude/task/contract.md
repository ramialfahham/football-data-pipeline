# Task contract — handover for the description-drift programme

objective: >
  Bring `.claude/active_work.md` current so a NEW CHAT can continue the description-drift
  programme at MR3 with zero re-investigation. MR1 (`!82`) and MR2 (`!83`) merged today; the
  handover still describes the 2026-08-19 Browse/team-names session as current and says nothing
  about the programme, its ordering constraints, or the traps that cost review rounds in MR1/MR2.
  Bookkeeping only — no code, no behaviour change.
refs: >
  Programme plan and authority: `.claude/task/escalations.log`, 2026-08-20 entry. Plan file:
  `C:\Users\Rami\.claude\plans\jazzy-greeting-teacup.md`. main `657e477`, no open MRs.

impact_map: >
  Trivial/leaf, evidenced. Only `.claude/active_work.md` and this contract are edited.
  `active_work.md` is a handover artifact read by humans and the SessionStart hook; it is in BOTH
  `review_exclude_paths` and `hash_exclude_paths` in `.claude/review_routing.json` and matches
  `artifact_only`. No model, mart, seed, export, site or test file is touched — zero warehouse
  blast radius, zero build impact.

  ⚠ NOT artifact-exempt from review, and the distinction caught me out last time: staging
  `contract.md` puts the commit in `artifact_only_never`, so a review round IS required however
  trivial the diff. `active_work.md` alone would have been exempt. Routing gives scope-auditor
  only — no path here matches a specialist glob.

scope_paths:
  - .claude/active_work.md
  - .claude/task/contract.md

decisions_taken: >
  CPO, in chat, 2026-08-20: "but prepare handover, we'll continue in a new chat", given after
  approving MR3 to proceed. The handover is therefore written so the NEXT chat starts MR3, not so
  this one does.

decisions_reserved:
  - MR3 itself is not started here. The handover records what it must do and the constraints on
    it; it does not pre-empt any judgement the next session owes.
  - The 4 surviving "partition key" instances are recorded as MR3/MR4 work, not fixed here.

done_when:
  - `active_work.md` names main `657e477`, states no open MRs, and marks MR1/MR2 merged.
  - It points at `escalations.log`'s 2026-08-20 entry and the plan file as the authority, with an
    explicit instruction not to re-scope or re-audit.
  - It carries the six-MR table with the two ordering constraints (MR5 after 3-4 for a green gate;
    MR6 after 3-4 because 15 descriptions exceed BigQuery's 1,024-char limit).
  - It records the four traps hit for real in MR1/MR2, each with enough detail to avoid repeating.
  - Under the 16,000-CHARACTER cap, measured with Python `len()` (never `wc -c`, which is bytes).
  - Committed; MR opened by the post-commit hook.

amendments:
  - none
