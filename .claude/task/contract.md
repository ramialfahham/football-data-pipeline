# Task contract — Handover refresh (2026-06-22 close-out: players re-grain)

objective: >
  Refresh .claude/active_work.md to the true post-merge state. This session: (1) the Phase 2a deep
  RESUME (CPO Option A) is DONE — CAFCL/LIBER/CWC are at MAX PROVIDER DEPTH (the year-count "gaps"
  were API-Football catalog floors, not ingest misses); all 15 Phase 2a leagues are at their
  configured/available depth. (2) The resume surfaced a real loader bug — RAW_APIF_PLAYERS crammed a
  whole league's players into one >100MB BigQuery row (LIBER/UEL/UCL failed) — fixed by re-graining to
  one merge-on-write row per (team,season) (the RAW_APIF_FIXTURE_DETAILS pattern): PR #536 MERGED, the
  existing data re-shaped in place (413,755 player-team-seasons preserved). #534 (chunking) closed.
  (3) #518 updated with the diagnosis-drift recurrence + proposed enforcement. Set the FIRST next action.

refs: >
  This conversation 2026-06-22. PR #536 (merged), #534 (closed), #518 (process retrospective updated).
  Memory: feedback-no-hacky-solutions (5th mode — end-to-end-map-first).

scope_paths:
  - .claude/active_work.md
  - .claude/task/**

decisions_taken: >
  Documentation-only handover refresh — no code, no product decision. The commit carries contract.md
  (hashed, not artifact-exempt), so it needs review; routing for active_work.md + .claude/task/** is
  scope-auditor only. active_work.md is hash-excluded (artifact). No code paths touched.

done_when:
  - active_work.md reflects: #536 merged (players merge-on-write per (team,season); main green);
    Phase 2a resume done (all 15 at provider depth; gaps were catalog floors); #534 closed; #518
    updated; the end-to-end-map-first lesson; FIRST next action set.
  - Tree matches the contract (only active_work.md + .claude/task/**).
