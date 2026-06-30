# Task contract — refresh handover: #391 GAP-01 merged (#613), Phase B spec'd screens complete

> Written on a CLEAN tree (branch chore/refresh-handover-613 off main @ f4b1aa8).
> Doc-only — no code/model change. Records this session's state for a cold chat.
> See docs/working_agreement.md §2 (contract), §10 (decision rights).

objective: >
  Refresh .claude/active_work.md so a fresh chat continues from the post-#613 state: #391 GAP-01 (team
  founded year + venue) MERGED as #613. Phase B's spec'd-screen gaps are now COMPLETE (the 3 spec'd screens
  01 fixture / 02 team / 03 player are data-complete). Set the next action = CPO pick among Phase C
  (player-season foundation), Phase D (flagship design marts), and a doc-status reconciliation pass.

refs: >
  This session (2026-06-30): GAP-14 (#609) → handover (#610) → GAP-16 (#611) → handover (#612) → GAP-01
  (#613). GAP-01 = the register's 4 fields (founded + venue name/city/capacity), mart+export, folded
  wireframe/register doc-sync (3rd CPO-directed fold). Mirrors prior handover refreshes.

scope_paths:
  - .claude/active_work.md
  - .claude/task/**

decisions_taken: >
  Documentation / handover only — RECORDS this session's STATE for a cold chat: GAP-01 merged (#613), Phase
  B's spec'd-screen gaps complete, and the FACT that #613's doc-sync was folded in at the CPO's explicit
  per-PR direction (the 3rd instance after #609/#611). Per-PR §10 items (GAP-01's field-set ruling; the
  payload shape; the doc-sync fold) are owned + evidenced in #613's own review.md, not re-decided here.
  Asserts NO governance reinterpretation (the "does folding generalize" question stays OPEN — see
  decisions_reserved) and invents no product/metric/naming decision.

decisions_reserved:
  - The next track — CPO directs; none auto-granted. No spec'd-screen Phase-B items remain. Candidates:
    Phase C (player-season foundation chain, #480 → backfill, §10 depth+cost), Phase D (flagship design
    marts — opponent/schedule context + contribution-share, §10 method/definition), and the doc-status
    reconciliation (below).
  - DOC-STATUS reconciliation (a doc-only pass, CPO-directed): the 02 wireframe §10 still lists GAP-15 as
    open (it shipped via #607); content_architecture.md §3's status column has drifted since 2026-06-17. A
    sweep to reconcile shipped-gap status across the wireframes + content_architecture.
  - The open governance question — whether folding a closed gap's directly-coupled spec-sync into its gap
    PR GENERALIZES (now 3 CPO-directed instances: #609/#611/#613) vs the gaps-register "gap fixes never
    ship inside blueprint PRs" note — stays OPEN, reserved to the CPO. Not decided here.
  - The two stale-wireframe reconciliations (02 block-5 ratio-space vs the shipped rank-space;
    finishing_efficiency [0,1] vs the "never capped" line) — flagged, not decided.

done_when:
  - active_work.md states main @ f4b1aa8 (GAP-01 #613 merged); records the data-first #391 strategy, that
    Phase B's spec'd screens are complete (A1/GAP-15/GAP-14/GAP-16/GAP-01 done), the next-track candidates
    (Phase C/D + the doc reconciliation), the still-open fold question (3 instances), the two stale-wireframe
    flags, and the standing rules.
  - scope-auditor PASS (>=2 risks); review.md diff_sha256 binds the staged diff; CPO merges.

amendments: (none)
