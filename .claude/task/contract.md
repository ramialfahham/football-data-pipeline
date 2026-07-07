# Task contract — Team → Stats (vs-league benchmark) wireframe spec (#391)

> Written on a CLEAN tree (branch docs/391-team-stats-benchmark-spec off main @ f35b99f).
> Plan approved via ExitPlanMode this session. Doc-only wireframe SPEC (the #625 player-Stats pattern) —
> the export wiring is a SEPARATE follow-up PR, registered here as GAP-23.

objective: >
  Spec the Team → Stats (vs-league) sub-screen — a new wireframe `docs/wireframes/14_team_stats.md`,
  field-bound to the built-but-orphaned `mart_team_competition_benchmarks`. CPO decision this session: a SEPARATE
  Team → Stats sub-screen (not an in-place enrichment of the profile's single-value season-metrics block),
  mirroring the player Stats screen (12). Rank-based ("k of N" + vs-median + p25/median/p75 spread bar, honest at
  league N≈18 — never percentile, per metrics_display.md), direction-aware from the catalogue (only
  `goals_against_per_match` is lower_better → rank mirrored), no position dimension (season selector only), the 20
  team metrics grouped by the metrics_display block order. Ratios use the adjacent-count-row no-naked-% mechanism
  (team convention). This is the SPEC; export wiring = GAP-23 (a later PR).
refs: #391; mart_team_competition_benchmarks (built); 12_player_stats.md + #625/#627 (player precedent); metrics_display.md (LOCKED); content_architecture §3 "Vs-benchmark · team orphan".

scope_paths:
  - docs/wireframes/**
  - .claude/task/**

impact_map: >
  Doc-only, no structural surface. New wireframe `docs/wireframes/14_team_stats.md` + companion doc-syncs
  (00_overview inventory/census, 99_gaps_register GAP-23, 02_team_profile §10 ▸Stats link). No dbt model, no
  scripts/**, no ingestion — zero data/number/metric/build impact. The wireframe is field-bound to REAL columns
  of `mart_team_competition_benchmarks` (verified: metric_value, rank, team_count, league_median/mean/p25/p75,
  vs_median_delta; metric set = the 20 metric_keys in int_team_competition_benchmark_metrics_long) — a binding
  doc, not a consumer. contract.md is artifact_only_never → scope-auditor required.

decisions_taken: >
  CPO-approved via the plan: (1) a separate Team → Stats sub-screen; (2) rank-based display ("k of N" + vs-median
  + spread bar), which metrics_display.md already declares for the team benchmark — not a new invention; (3) the
  20-metric set + block order come from the shipped mart + the LOCKED metrics_display contract; (4) directions
  from the catalogue (verified). No new metric, no new mechanism. The board flip is NOT taken here — the
  team-benchmark row goes green only when WIRED (GAP-23), not at spec.

decisions_reserved:
  - The export wiring (GAP-23) — a separate follow-up PR (the #627 analog); NOT this change.
  - Spread-bar colour — deferred to the design pass (#366).
  - `save_ratio` naked % (no count peer in the set) — a catalogue matter (GAP-11 family), not this screen.

done_when:
  - docs/wireframes/14_team_stats.md exists, §1–10, every §5 row bound to a real mart column, rank rule +
    direction mirror + floor + no-colour rules internally consistent with 12 + metrics_display.
  - Companion doc-syncs: 00_overview (screen 14 + census), 99_gaps_register (GAP-23 export wiring), 02 §10 link.
  - No board flip (green only on wiring); no code/model/data change.
  - scope-auditor + bi-analyst-reviewer PASS (>=2 named risks each); review.md diff_sha256 binds; CPO merges.

amendments: (none)
