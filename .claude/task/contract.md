# Task contract — Handover refresh (2026-06-22 close-out: #539 merged)

objective: >
  Refresh .claude/active_work.md after PR #542 (#539) merged. #539 codified the read-all staging
  class in layering.md §1_staging accurately (sub-league grain → read all rows, no league_code
  qualify, base resolves current-per-entity; incremental-accumulation + merge-on-write as the two
  loader reasons; RAW_APIF_FIXTURE_DETAILS and RAW_APIF_PLAYERS both bounded one-row-per-key — the
  corrected, source-verified premise) and gave the four fixture-detail staging models the header +
  yml read-all rationale. It was the first real exercise of the #540 impact-map gate. Update the
  status line + FIRST-next-session (drop the #539 follow-up — now done); main green.

refs: >
  This conversation 2026-06-22. PR #542 (merged, #539). Prior this session: #540 (impact-map gate),
  #541 (handover). Memory: feedback-no-hacky-solutions (the trace-first discipline caught #539's own
  premise being wrong before it hit the authoritative doc).

scope_paths:
  - .claude/active_work.md
  - .claude/task/**

decisions_taken: >
  Documentation-only handover refresh — no code, no product decision. The commit carries
  contract.md (hashed, not artifact-exempt), so it needs review; routing for active_work.md +
  .claude/task/** is scope-auditor only. active_work.md is hash-excluded (artifact).

decisions_reserved:
  - none. Pure handover bookkeeping.

done_when:
  - active_work.md reflects: #542 merged (#539 read-all staging codification + corrected premise);
    the #539 follow-up removed from the #518 bullet; main green; FIRST next action set.
  - Tree matches the contract (only active_work.md + .claude/task/**).

amendments: (none)
