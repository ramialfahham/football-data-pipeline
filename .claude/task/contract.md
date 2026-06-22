# Task contract — Handover restructure into two tracks (2026-06-23 close-out)

objective: >
  Restructure .claude/active_work.md from a flat list into the CPO-approved two-track operating model:
  PRODUCT (primary) + PROGRAMS (coverage #545 / data-quality #546 / cost #547), so the new
  domestic-league expansion program does not eclipse product work and a fresh chat inherits both
  tracks + the current mix. Also bring the handover current: PRs #540/#542/#544 merged, #510/#539
  closed, and today's deep #526 investigation (provider duplicate-team-id quirk; data complete/
  uncorrupted; the clubs are thin only because we ingest them via continental cups, not their domestic
  leagues) which seeded the three program epics + the stream:* labels. Set FIRST next action by track.

refs: >
  This conversation 2026-06-22/23. Created today: epics #545 (coverage), #546 (data-quality, seeded by
  #526), #547 (cost); stream:* labels. #526 fix still OPEN (canonicalization decision pending).

scope_paths:
  - .claude/active_work.md
  - .claude/task/**

decisions_taken: >
  Documentation-only handover refresh — no code, no product decision. The commit carries contract.md
  (hashed, not artifact-exempt) so it needs review; routing for active_work.md + .claude/task/** is
  scope-auditor only. active_work.md is hash-excluded (artifact). The two-track model + the three
  program epics were CPO-approved this session ("Do it").

decisions_reserved:
  - none. Pure handover bookkeeping + structure. (#526's fix and the coverage tranche cut are
    escalated on their issues, not decided here.)

done_when:
  - active_work.md carries: a 2026-06-23 status line; a "How work is organized — two tracks" section
    (PRODUCT primary + PROGRAMS #545/#546/#547 with stream:* labels); a FIRST-next-session organized
    by track (programs: #545 tranche pick, #526 fix decision, #546 scan, #547 sizing; product: the
    content_architecture roadmap); the durable reference sections retained.
  - Tree matches the contract (only active_work.md + .claude/task/**).

amendments: (none)
