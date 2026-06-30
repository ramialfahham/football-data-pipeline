# Task contract — refresh handover: #391 GAP-16 merged (#611), Phase B nearly done

> Written on a CLEAN tree (branch chore/refresh-handover-611 off main @ aea472f).
> Doc-only — no code/model change. Records this session's state for a cold chat.
> See docs/working_agreement.md §2 (contract), §10 (decision rights).

objective: >
  Refresh .claude/active_work.md so a fresh chat continues from the post-#611 state: #391 GAP-16 (player
  team affiliation — current team + per-season history) MERGED as #611. Update the Phase-B backlog (A1 #606,
  GAP-15 #607, GAP-14 #609, GAP-16 #611 all merged; only GAP-01 remains on the spec'd screens) and set the
  next action = CPO pick (GAP-01, which needs a disposition ruling first, or move to Phase C/D).

refs: >
  This session (2026-06-30): GAP-14 (#609) → handover (#610) → GAP-16 (#611). GAP-16 source = Option B
  (most-recent-finished-match team, dbt-derived; CPO-ruled), int_player_season__team + mart + DQ + export +
  folded wireframe/register doc-sync (CPO-directed). Mirrors prior handover refreshes (#610, #608, #605...).

scope_paths:
  - .claude/active_work.md
  - .claude/task/**

decisions_taken: >
  Documentation / handover only — RECORDS this session's STATE for a cold chat: GAP-16 merged (#611), the
  Phase-B backlog status, and the FACT that #611's doc-sync was folded in at the CPO's explicit per-PR
  direction (the 2nd instance after #609). Per-PR §10 items (GAP-16's Option-B source ruling; the naming;
  the doc-sync fold) are owned + evidenced in #611's own review.md, not re-decided here. Asserts NO
  governance reinterpretation (the "does folding generalize" question stays OPEN — see decisions_reserved)
  and invents no product/metric/naming decision.

decisions_reserved:
  - The next item — CPO directs; none auto-granted. Remaining spec'd-screen Phase-B = GAP-01 (team venue/
    founded fields, mart+export; disposition still "pending" — needs a §10 ruling before a clean start).
    Beyond that: Phase C (player-season foundation chain) / Phase D (flagship design marts).
  - The open governance question — whether folding a closed gap's directly-coupled spec-sync into its gap
    PR GENERALIZES (now 2 CPO-directed instances: #609 status-only, #611 substantive) vs the gaps-register
    "gap fixes never ship inside blueprint PRs" note — stays OPEN, reserved to the CPO. Not decided here.
  - The two stale-wireframe reconciliations (02 block-5 ratio-space vs the shipped rank-space;
    finishing_efficiency [0,1] vs the "never capped" line) — flagged, not decided. (03-player staleness was
    resolved by #609 + #611.)

done_when:
  - active_work.md states main @ aea472f (GAP-16 #611 merged); records the data-first #391 strategy, the
    updated backlog (A1/GAP-15/GAP-14/GAP-16 done; GAP-01 the last spec'd Phase-B item), GAP-16's Option-B
    source + the doc-sync FACT, the still-open fold-generalization question, the two stale-wireframe flags,
    and the standing rules.
  - scope-auditor PASS (>=2 risks); review.md diff_sha256 binds the staged diff; CPO merges.

amendments: (none)
