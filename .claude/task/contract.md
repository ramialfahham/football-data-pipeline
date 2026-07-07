# Task contract — reconcile content_architecture.md §3/§7 board to reality (post-#648)

> Written on a CLEAN tree (branch chore/reconcile-content-arch-post-648 off main @ 712f16b).
> Doc-only status reconciliation (the #615/#620/#636 pattern) — flip stale board markers to match shipped
> reality. Plan mode skipped (doc-sync/bookkeeping + CPO's explicit go); contract + review + gate run.
> Scoped to content_architecture.md ONLY (NOT active_work.md) so it cannot conflict with the open #661.
> Required reviewer (routing): scope-auditor only.

objective: >
  Re-reconcile `docs/content_architecture.md` §3 (block↔mart board) + §7 (new-mart status) to the shipped state —
  the legend was last reconciled 2026-07-02 (post-#634) and predates #638/#645/#648. Flip the stale markers:
  the player **Season** block (per-club foundation shipped #630, wired via mart_player_profile), player
  **Season-over-season/YoY** (#638 + #648), and **Contribution-share** (#645, catalogued) are now ✓; correct the
  **Opponent/schedule context** flagship from "✗ not built" to "✗ SHELVED 2026-07-03" (no display home); note
  player **Streaks** SKIPPED (CPO 2026-07-03); update the Career "thin/needs backfill" notes (backfill effectively
  done, 5–10 seasons deep). The **team benchmark** stays ⚠ orphan (built, not wired, screen unspec'd) — unchanged.
refs: #630 (#480 §8.3); #638 + #648 (player YoY); #645 (contribution-share); opponent-context SHELVED 2026-07-03; player streaks SKIPPED 2026-07-03.

scope_paths:
  - docs/content_architecture.md
  - .claude/task/**

impact_map: >
  Doc-only, no structural surface. `docs/content_architecture.md` is prose governance (a block/mart board), not
  referenced by any model or the export — editing it changes no compiled SQL, no data/number/metric, no build. No
  dbt_project/**, no scripts/**, no ingestion/**. contract.md is artifact_only_never → scope-auditor required.

decisions_taken: >
  Record-only. Every flip reflects work already merged (#630/#638/#645/#648) or a CPO ruling already made
  (opponent-context SHELVED 2026-07-03, player streaks SKIPPED 2026-07-03, backfill-effectively-done finding).
  Invents no new status; the team-benchmark orphan and the un-spec'd screens stay exactly as they are.

decisions_reserved:
  - Whether/when to wire the team benchmark (needs its screen spec'd first) — unchanged, a later CPO pick.
  - The remaining foundation tail (GAP-07 report pages, GAP-17 MVP denominators) — untouched here; still open.

done_when:
  - §3 legend date + note bumped to post-#648; player Season / Season-over-season / Contribution-share rows show ✓
    with the shipping PR; Opponent-context marked SHELVED; player Streaks noted SKIPPED; Career "backfill" notes
    updated; team benchmark stays ⚠ orphan.
  - §7 status date bumped; Career "needs backfill" note updated.
  - No mart-count change (17 — #638/#645/#648 enrich mart_player_profile, add no new wired mart).
  - scope-auditor PASS (>=2 named risks); review.md diff_sha256 binds; CPO merges.

amendments: (none)
