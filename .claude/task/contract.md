# Task contract — refresh handover: #391 GAP-14 merged (#609), Phase B continues

> Written on a CLEAN tree (branch chore/refresh-handover-609 off main @ 2b9f656).
> Doc-only — no code/model change. Records this session's state for a cold chat.
> See docs/working_agreement.md §2 (contract), §10 (decision rights).

objective: >
  Refresh .claude/active_work.md so a fresh chat continues from the post-#609 state: #391 GAP-14
  (player birth_date → v2 player payload) MERGED as #609. Update the Phase-B gap-backlog status
  (A1 #606, GAP-15 #607, GAP-14 #609 all merged; GAP-16 + GAP-01 remain) and set the next action =
  CPO pick. Replaces the prior handover that still listed GAP-15 as "PR #607 open" and predated GAP-14.

refs: >
  This session (2026-06-30): Phase-B pick = GAP-14 (CPO); built export-only, then folded the wireframe/
  gaps-register doc sync in per CPO go ("fix that doc too, now, in the same change"); merged as #609.
  Mirrors prior handover refreshes (#608/#607, #605/#604, #602, #599).

scope_paths:
  - .claude/active_work.md
  - .claude/task/**

decisions_taken: >
  Documentation / handover only — RECORDS this session's STATE for a cold chat: GAP-14 merged (#609) and the
  Phase-B backlog status. It records the FACT that #609 ALSO carried the directly-coupled wireframe +
  gaps-register doc sync, folded into the same PR at the CPO's explicit per-PR direction ("fix that doc too,
  now, in the same change") — a specific instruction for #609, NOT a general rule. Per-PR §10 items (GAP-14's
  key name `birth_date`; the doc-sync fold) are owned + evidenced in #609's own review.md, not re-decided
  here. Asserts NO governance reinterpretation and invents no product/metric/naming decision.

decisions_reserved:
  - Whether folding a closed gap's directly-coupled spec-sync into its gap PR GENERALIZES beyond #609 — and
    how that squares with the gaps-register note "gap fixes never ship inside blueprint PRs" — is an OPEN
    governance question, reserved to the CPO. #609 was a specific CPO direction, not a precedent that settles
    the general rule; the handover flags it open, does not decide it.
  - The next Phase-B (or Phase-C/D) item — CPO directs; none auto-granted. Remaining spec'd-screen Phase-B:
    GAP-16 (player current-team affiliation, dbt-derived) and GAP-01 (team venue fields, mart+export —
    disposition still "pending", needs a §10 ruling before a clean start).
  - Whether to spec the orphan-mart screens (Squad / Stats-percentile / Career) — wireframe/design, CPO call.
  - The two stale-wireframe reconciliations (02 block-5 ratio-space vs the shipped rank-space;
    finishing_efficiency [0,1]/Option A vs the "never capped" line) — flagged, not decided.

done_when:
  - active_work.md states main @ 2b9f656 (GAP-14 #609 merged); records the data-first #391 strategy, the
    updated backlog (A1 #606 / GAP-15 #607 / GAP-14 #609 done; GAP-16 + GAP-01 remaining), the #609 doc-sync
    FACT + the open generalization flag, the two stale-wireframe flags, and the standing rules.
  - scope-auditor PASS (>=2 risks); review.md diff_sha256 binds the staged diff; CPO merges.

amendments: (none)
