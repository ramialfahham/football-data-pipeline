# Task contract — refresh handover: #530(a) merged, #391 conversation next

> Written on a CLEAN tree (branch chore/handover-refresh-530a-merged off main @ 6dd1f89).
> Doc-only — no code/model change. Records merged state; invents no decision.

objective: >
  Refresh .claude/active_work.md so a fresh chat continues from the current merged state:
  #530(a) (split the 2 entity-dual catalogue rows finishing_efficiency + duels_won_pct per entity)
  is MERGED (#604, main @ 6dd1f89). The CPO-agreed next step is the #391 conversation — whether to
  un-pause the website so the metric layer gets a user-facing consumer — a DISCUSSION, not a build.
  Update status + next action + do-NOTs; carry forward the #530 follow-ups ((b) player goals_penalty
  leg + the 3 deferred player rows; (c) model-conformance test) and the stale-wireframe note.

refs: >
  Follows #604 (the #530(a) split, merged this session). Mirrors prior handover refreshes (#599, #602).
  CPO directed this refresh in-chat (2026-06-29).

scope_paths:
  - .claude/active_work.md
  - .claude/task/**

decisions_taken: >
  Documentation / handover only — RECORDS merged state and the CPO's standing in-chat decision (the
  #391 conversation is next, as a discussion). Invents no product/metric/naming decision. Does NOT
  start #391 product work, nor decide the #530(b)/(c) sequencing, nor reconcile the stale wireframe
  line — all reserved to the CPO.

decisions_reserved:
  - The #391 un-pause outcome (un-pause product vs continue foundation) — the CPO's call, after the discussion.
  - #530(b) sequencing (add goals_penalty to int_legs__player_match, then fill the 3 deferred player rows).
  - Whether/when to reconcile the stale "never capped" wireframe line (metrics_display.md:107) to Option A [0,1].

done_when:
  - active_work.md states #530(a) MERGED (#604, main @ 6dd1f89), names the #391 conversation as the
    CPO-agreed next step (DISCUSSION not build), and carries the #530(b)/(c) follow-ups + the stale-wireframe note.
  - scope-auditor PASS (>=2 risks); review.md diff_sha256 binds the staged diff; CPO merges.

amendments: (none)
