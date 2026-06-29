# Task contract — lock #530(a) as next task + record the #391 conversation (handover refresh)

> Handover refresh. Written on a CLEAN tree (main @ a3bc9c3). Doc-only — no code/model change.

objective: >
  Refresh .claude/active_work.md so a fresh chat continues with the CPO's just-made decision:
  (1) the LOCKED next task is #530(a) — split the 2 entity-dual catalogue rows (finishing_efficiency,
  duels_won_pct) into per-entity rows with explicit base_relation + *_expr; (2) the CPO-agreed move
  AFTER (a) is the #391 conversation (whether to un-pause product so the metric layer gets a
  user-facing consumer). Catalogue-first; the per-entity exprs + the (a)/(b) sequencing are §10 — do
  not pre-decide. No code change.

refs: >
  CPO decision this chat: "First (a) then #391 -> yes." (a) = the lead #530 follow-up from the #600
  handover. Mirrors prior handover refreshes (#602, #599).

scope_paths:
  - .claude/active_work.md
  - .claude/task/**

decisions_taken: >
  Documentation / handover only — RECORDS the CPO's in-chat decision (lock (a); #391 conversation
  next), invents none. Does NOT decide the per-entity exprs for the split, nor the (a)/(b)
  sequencing, nor the #391 outcome — all reserved to the CPO at build/discussion time.

decisions_reserved:
  - The per-entity base_relation + numerator_expr/denominator_expr for finishing_efficiency and
    duels_won_pct (a §10 metric-formula decision — catalogue-first sign-off in the new chat).
  - Whether finishing_efficiency-player waits on #530(b) (player goals_penalty leg) — the two are
    entangled (player open-play = goals_total - goals_penalty, and player goals_penalty is the
    deferred (b) row). The new chat surfaces the sequencing to the CPO.
  - The #391 un-pause outcome (product vs continued foundation) — the CPO's call, after (a).

done_when:
  - active_work.md names #530(a) as the LOCKED next task (catalogue-first: design proposal -> CPO
    sign-off -> plan mode -> build), flags the (a)/(b) entanglement, and records the #391 conversation
    as the CPO-agreed next-after.
  - scope-auditor PASS (>=2 risks); review.md diff_sha256 binds the staged diff; CPO merges.

amendments: (none)
