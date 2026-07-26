# Task contract — handover refresh (foundation build handoff to a new chat)

> Written on a CLEAN tree (branch `docs/handover-foundation-build` off main at fb3a1a4).
> Bookkeeping: refresh the single handover so a fresh chat starts the frontend FOUNDATION build
> with zero re-investigation. No code, no model change.

objective: >
  Rewrite .claude/active_work.md to the true current state so a new chat can begin the frontend
  FOUNDATION build immediately: the 2026-07-26 spec audit found the frontend systematic on data/
  content but improvisational on layout/chrome/workflow; CPO decided foundation-first + lean process;
  the shared-frame design is APPROVED via mock (artifact 87d14109; home-content mock 1c35e7aa); the
  build = turn the mock into the real Layout.astro shell + system.css responsive system + write the
  two missing specs (09_chrome + a layout section), composing ONLY from the locked system.css. Carry
  ALL owed items and the design discipline. Keep CURRENT STATE ONLY and under 16,000 characters.

refs: >
  This session 2026-07-26. Frontend spec audit + backtobayesics process study (both agent runs).
  CPO decisions this session: widen desktop to ~1100px two-column; foundation-first + lean process;
  foundation mock "looks good for now". Firebase deploy merged (#821), effort pins merged (#822),
  prior handover merged (#823) — main now fb3a1a4.

scope_paths:
  - .claude/active_work.md

decisions_taken: >
  Pure bookkeeping. All facts recorded are already true (audit done, CPO decided foundation-first +
  lean process, foundation mock approved). No new product/metric/mechanism decision is made here.

decisions_reserved:
  - The foundation's open design questions (nav contents/order, search style, per-page rail contents,
    footer/legal, default-theme policy) remain the CPO's §10 calls — recorded in the handover as
    reserved, not decided here.

done_when:
  - .claude/active_work.md leads with the foundation-build task (design approved, build not started),
    carries every OWED item and ⚠️ warning intact, records the audit + foundation-first/lean-process
    decision + design discipline + mock URLs, and stays under 16,000 chars.
  - ONE commit; review.md with scope-auditor PASS; pushed with an explicit refspec; PR opened. CPO merges.

amendments: (none)
