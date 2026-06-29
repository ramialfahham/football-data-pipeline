# Task contract — refresh handover: #391 un-paused (data-first), gap backlog A–D, A1 merged + GAP-15 PR'd

> Written on a CLEAN tree (branch chore/handover-refresh-391-backlog off main @ 5041396).
> Doc-only — no code/model change. Records this session's decisions + state for a cold chat.

objective: >
  Refresh .claude/active_work.md so a fresh chat continues from this session's big shift: the CPO
  un-paused #391 NARROWLY with a data-first strategy — complete the v2 data+export layer to "all green"
  first, then build the frontend. Records the verified block→mart→status gap map, the A–D gap-closure
  backlog (A1 MERGED #606; GAP-15 = first Phase-B item, PR #607 open; the rest queued), the two stale-
  wireframe flags, and the standing rules. Replaces the prior "#391 is a discussion" handover.

refs: >
  This session (2026-06-29): #391 un-pause discussion → data-first strategy; A1 (#606, MERGED);
  GAP-15 (#607, open). CPO directed this refresh ("fold the handover refresh in after"). Mirrors
  prior handover refreshes (#605/#604, #602, #599).

scope_paths:
  - .claude/active_work.md
  - .claude/task/**

decisions_taken: >
  Documentation / handover only — RECORDS this session's STATE for a cold chat: the CPO's un-pause of
  #391 (data-first), the A–D backlog, the verified gap map, and the orphan-marts-need-screen-specs
  methodology note. Per-PR §10 decisions (A1's Option-1 placement; GAP-15's payload key names) are owned
  and evidenced in those PRs' own review cycles (#606, #607), not re-decided here. Invents no new
  product/metric/naming decision.

decisions_reserved:
  - The next Phase-B item after GAP-15 (GAP-14 player birth_date / GAP-16 player affiliation / GAP-01
    venue) — CPO directs; none auto-granted.
  - Whether to spec the orphan-mart screens (Squad / Stats-percentile / Career tabs) so benchmarks/
    roster/career can be wired — wireframe/design work, CPO call.
  - The two stale-wireframe reconciliations (block-5 deserved-vs-actual ratio-space vs the shipped
    rank-space; finishing_efficiency [0,1]/Option A vs the "never capped" line) — flagged, not decided.

done_when:
  - active_work.md states main @ 5041396 (A1 #606 merged), GAP-15 #607 open; records the data-first
    #391 strategy, the verified gap map (3 spec'd screens; orphan marts blocked on screen specs), the
    A–D backlog with status, the two stale-wireframe flags, and the standing rules.
  - scope-auditor PASS (>=2 risks); review.md diff_sha256 binds the staged diff; CPO merges.

amendments: (none)
