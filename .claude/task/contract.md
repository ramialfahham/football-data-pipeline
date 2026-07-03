# Task contract — handover refresh (post-#645, Phase D bonus contribution-share merged)

> Written on a CLEAN tree (branch chore/handover-refresh-post-645 off main @ a08c634).
> Bookkeeping only — brings `.claude/active_work.md` current from its stale post-#643 state (pointer 87598cc)
> to post-#645 (a08c634). No code, no model, no metric change. Plan mode skipped per the CPO handover carve-out
> (2026-06-30); still runs the contract + review + gate.

objective: >
  Refresh the handover: record #645 (Phase D bonus — player contribution-share `int_player_profile__contribution`
  composed into mart_player_profile + catalogued contribution_share) as MERGED; bump the main-GREEN pointer
  87598cc -> a08c634; record that Phase C brick 2 (player streaks) is SKIPPED (CPO, 2026-07-03); leave NEXT as
  an open CPO pick over the narrowed candidates (Phase D flagship opponent/schedule context + smaller carryovers).

refs: #645 (a08c634 Phase D bonus contribution-share); prior refresh c375a99 (post-#643)

scope_paths:
  - .claude/active_work.md
  - .claude/task/**

impact_map: >
  Doc/bookkeeping only. The single substantive file is `.claude/active_work.md` (the handover). No
  dbt_project/** model, no scripts/export_*.py, no ingestion/**, no site*/ change — so no data/number/metric
  moves and no downstream build impact. The task scaffolding (.claude/task/**) is artifact-only; contract.md is
  artifact_only_never so this commit is NOT review-exempt (scope-auditor required).

decisions_taken: >
  Record-only. #645 is already merged to main (a08c634) — this refresh does not decide anything new. Player
  streaks (Phase C brick 2) recorded as SKIPPED per the CPO (2026-07-03, this session). NEXT stays an OPEN CPO
  pick — no next task is locked in.

decisions_reserved:
  - The actual next task (Phase D flagship opponent/schedule context method is §10; smaller carryovers) — CPO picks later.

done_when:
  - active_work.md header + FIRST STEPS point at a08c634; #645 recorded as the latest merged PR.
  - The Phase D backlog entry marks the contribution-share bonus DONE #645; Phase C marks streaks SKIPPED.
  - A #645 entry is prepended to RECENT PRs; the "main carries" line appends #645.
  - scope-auditor PASS (>=2 named risks); review.md diff_sha256 binds; CPO merges.

amendments: []
