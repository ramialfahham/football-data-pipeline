# Task contract — handover refresh (end of session 2026-06-26)

> Governance G2/G3 contract. Written on a clean tree BEFORE any edit.
> Artifact/doc task — `.claude/active_work.md` is NOT auto-editable, so it is named in scope_paths.

objective: >
  Refresh `.claude/active_work.md` to the current truth: #576 (Confirm-step protocol) and #577
  (#500 PR2 player metric-layer renames) are MERGED; record the now-live Explore->Plan->Confirm->
  Implement->Verify protocol (plan mode = the Confirm gate), the #500 status (PR1 team + PR2 player
  DONE; PR-c docs / PR-d live-merge / mart-rename sweep remain), the new pending bq rm of the 4
  orphaned old PLAYER relations, and the candidate next units — so a cold chat continues frictionlessly.
refs: #500; #576; #577; end-of-session handover.

scope_paths:
  - .claude/active_work.md

decisions_taken: >
  Documentation only — no product/code/§10 decision. Records decisions already made and merged this
  session (the protocol b+c1 per CPO 2026-06-26; the PR2 four renames, renames-only).

decisions_reserved:
  - None new. (The bq rm of the 4 orphaned old player relations — and the still-pending 4 team
    relations from #574 — are CPO actions, bq rm being deny-listed. The next unit after #500 is a
    CPO direction, not pre-decided here.)

done_when:
  - .claude/active_work.md leads with: #576 + #577 MERGED; the protocol now LIVE (plan mode = Confirm);
    #500 PR1+PR2 done with PR-c/PR-d/mart-sweep as the remaining sequence; the candidate next units;
    the do-NOTs (CPO merges; don't break the live MVP; Bash only; contract-first); the pending bq rm.
  - Routes to scope-auditor only (active_work.md is in no routing path); PASS; commit carries
    contract.md so it is NOT artifact-exempt — scope-auditor must run. CPO merges.

amendments: (none)
