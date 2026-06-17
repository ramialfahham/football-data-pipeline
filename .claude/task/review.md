# Review — docs/content-architecture-spec — 2026-06-17

> NEW `docs/content_architecture.md` (the modular IA + data-architecture spec: blocks → tabs →
> navigation, flagship reads, new-mart map, backfill policy) + cross-link pointers in
> `site_architecture.md` and `metrics_context_model.md`. DOCS-ONLY; every build reserved to later PRs.
> Reviewers (CPO-directed for this data + IA content): scope-auditor + analytics-engineer-reviewer +
> bi-analyst-reviewer. One round of FAILs fixed: the player tier carve-out (display-contract
> contradiction), contribution-share "derive" → "mart-computed", percentile scope + per-tab block
> placements re-framed as reserved/proposed, and "transfers retired" → "no transfers tab". All PASS.

diff_sha256: ed18c9ad9de5b572d29e329d7e7bcdcbd5f0f5a6d63d73f8fa0c6a10ae947cfd

## scope-auditor
VERDICT: PASS
risks_checked:
- Reserved items are not silently decided: position-aware percentile, the contribution-share
  definition, and the exact per-tab block placements are all marked RESERVED / PROPOSED (not settled)
  — verified against the contract's decisions_reserved; each doc section traces to a decisions_taken entry.
- Scope + no stray edits: all hunks within scope_paths (the three docs + contract); the registry,
  metric_catalogue seed, locked metrics_display.md, and all models are untouched; the backfill
  registry change + ingest are explicitly deferred, not performed.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Block↔mart map verified against real models: every "✓" block traces to an existing mart
  (`mart_momentum__*`, `mart_fixture_stats__*`, `mart_season_record__*`, `mart_team_profile` incl.
  `performance_vs_results_gap`, standings, mapping); the new marts (benchmarks, leaderboards, roster,
  player_career, dim_coach) are realistic from data we have, with correct dependencies (benchmark →
  clean season agg; career → backfill; dim_coach → `RAW_APIF_COACHES`, which exists).
- Flagship reads map to real, computable metrics — deserved-vs-actual = the live
  `performance_vs_results_gap` (our honest chance-quality stand-in, no faked xG); YoY = the live team
  model; no fabricated metric. (Reviewed the initial diff; the subsequent fixes only clarified the
  consumption-layer — contribution-share → "mart-computed" — plus reserved framing and the transfers
  wording, all addressing points this review raised, so the PASS carries on the final diff.)

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- Density/tier rule now correctly carves out players: Principle 5 states team blocks = tier-1 compact
  but **player blocks have no tiers — per-surface rules** (citing the fixture top-players strip), which
  matches the locked `metrics_display.md` ruling verbatim. The earlier contradiction is resolved.
- Consumption-layer + metric governance respected: contribution-share is "mart-computed" (not
  export-derived); benchmark/percentile/contribution-share definitions are deferred to build-time
  catalogue + football-analytics; no new i18n string or display ruling is coined. The §4 tab
  compositions are explicitly "proposed", so the wireframe binding rule is not breached by an IA doc.

## escalations
(none)
