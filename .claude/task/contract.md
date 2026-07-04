# Task contract — handover refresh (post-#648, player YoY full-season reference merged)

> Written on a CLEAN tree (branch chore/handover-refresh-post-648 off main @ 1966d4d).
> Bookkeeping only — brings `.claude/active_work.md` current from post-#647-shelve state
> (pointer a6b90e9) to post-#648 (1966d4d). No code, no model, no metric change. Plan mode
> skipped per the CPO handover carve-out (2026-06-30); still runs the contract + review + gate.

objective: >
  Refresh the handover: record #648 (player YoY full-season prior-year reference —
  int_player_profile__yoy prev_full CTE + 6 *_prev_season_full context columns composed into
  mart_player_profile; a full >= pace-matched invariant DQ test; auto-carries to the v2 player
  export) as MERGED; bump the main-GREEN pointer a6b90e9 -> 1966d4d; record that the
  "enrich the YoY block" candidate is now DONE; leave NEXT as an open CPO pick over the
  remaining candidates (#530(b) player metric rows, #510, #484, or further player-season models).

refs: #648 (1966d4d player YoY full-season reference); prior refresh a6b90e9 (post-#647 shelve)

scope_paths:
  - .claude/active_work.md
  - .claude/task/**

impact_map: >
  Doc/bookkeeping only. The single substantive file is `.claude/active_work.md` (the handover). No
  dbt_project/** model, no scripts/export_*.py, no ingestion/**, no site*/ change — so no data/number/metric
  moves and no downstream build impact. The task scaffolding (.claude/task/**) is artifact-only; contract.md is
  artifact_only_never so this commit is NOT review-exempt (scope-auditor required).

decisions_taken: >
  Record-only. #648 is already merged to main (1966d4d) — this refresh does not decide anything new. The
  "enrich the existing YoY block" candidate (this session's pick) is recorded as DONE via #648. NEXT stays an
  OPEN CPO pick — no next task is locked in.

decisions_reserved:
  - The actual next task (further player-season models; or #530(b) / #510 / #484 carryovers) — CPO picks later.

done_when:
  - active_work.md header + FIRST STEPS point at 1966d4d; #648 recorded as the latest merged PR.
  - The Phase C backlog entry marks the YoY-enrichment DONE #648; NEXT candidate list drops the now-done item.
  - A #648 entry is prepended to RECENT PRs; the "main carries" line appends #648.
  - scope-auditor PASS (>=2 named risks); review.md diff_sha256 binds; CPO merges.

amendments: []
