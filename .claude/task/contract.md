# Task contract — rework the parked Player Stats percentile wireframe (#391, Stats-percentile screen)

> Written on a CLEAN tree (branch docs/391-player-stats-percentile-spec, fast-forwarded to main @ 8d38fc3).
> Doc-only (docs/wireframes/**). Continuation of an already-approved plan (ExitPlanMode), but the
> wording/scope changed — so the reworked spec is RESTATED to the CPO for the Confirm checkpoint before
> finalizing; full plan mode unless the CPO says skip. See docs/working_agreement.md §1.

objective: >
  The Player Stats percentile-vs-peers wireframe (docs/wireframes/12_player_stats.md) was DRAFTED, PARKED
  in a stash, and never merged (the draft is the version the CPO/bi-analyst flagged). #530(b)/#621 unblocked
  it (player finishing_efficiency + duels_won_pct now catalogued). Recover + REWORK the draft against the 4
  now-settled items, binding honestly to the shipped mart (mart_player_competition_benchmarks), and register
  the export-wiring GAP as its own later PR. Spec now → wire in a follow-up PR (the "cheap green" that
  follows). Last step to push mart_player_competition_benchmarks toward "built AND wired".

refs: >
  main @ 8d38fc3. Recovered from stash@{0} on this branch ("wip: 12_player_stats wireframe"). Mart is BUILT
  (player benchmark chain: #559 per-90 metric layer -> #561 engine + mart; entity-renamed in #500) but NOT
  carried by the export. Display contract banked in memory [[feedback-percentile-display-phrasing]].
  Sources verified this session: mart_player_competition_benchmarks.sql (columns/floor/grain),
  int_player_competition_benchmarks.sql (engine), macros/player_benchmark_metrics.sql (the 18-metric set +
  position eligibility), int_player_season_position__metrics.sql (per-90s + the ratio num/den atoms),
  metric_catalogue.csv (direction of all 18).

scope_paths:
  - docs/wireframes/12_player_stats.md
  - docs/wireframes/03_player_profile.md
  - docs/wireframes/00_overview.md
  - docs/wireframes/99_gaps_register.md
  - docs/wireframes/metrics_display.md
  - .claude/task/**

impact_map: >
  None — doc-only (docs/wireframes/**). No dbt model (dbt_project/models/**), no export (scripts/export_*.py),
  no ingestion (ingestion/**), no site (site*/) file is touched. The spec is written AHEAD of its wiring PR
  (same pattern as Squad/11 preceding #619); every §5 payload key is PROPOSED-pending GAP-21.

decisions_taken: >
  All four rework items are SETTLED/RESOLVED (banked memory [[feedback-percentile-display-phrasing]] +
  handover), so this records CPO decisions already made — it invents no §10:
  (1) Label = uniform ladder "top X% / median / bottom X%" — median-anchored distributional position;
      single-fill bar on a track + dashed median line; NO neutral band; NO good/bad colour (deferred to the
      #366 design pass). Median-band word = "median" (CONFIRMED CPO 2026-07-02; "middle"/"more than X%"/
      neutral+directional wording all dropped). Direction-aware inversion is DEFINED for any future
      lower_better metric so "top" marks the better end.
  (2) Bind all 18 benchmark metrics (macros/player_benchmark_metrics.sql): GK = {saves_per90, save_pct,
      passes_per90, pass_accuracy_pct}; DEF/MID/ATT = those + 12 more (goals, assists, scorer points, shots
      on target, key passes, finishing, dribbles count+%, duels won count+%, defensive actions, tackles,
      interceptions, blocks) — each ranked within its own position group. Peers = position group.
  (3) Restore the "Top scorers" link on 03_player_profile.md (an earlier edit dropped it) + add the Stats link.
  (4) The 5 ratio metrics (save_pct, pass_accuracy_pct, finishing_efficiency, dribbles_success_pct,
      duels_won_pct) render the volume triple {num} of {den} · {pct}% (no naked %). The num/den atoms EXIST
      in int_player_season_position__metrics; the GAP-21 wiring PR must carry them into the payload.
  (5) Register GAP-21 — wire mart_player_competition_benchmarks into shape_player_payload (a later export-only
      PR; the "cheap green").
  HONEST-BINDING CORRECTION (not a new decision — a factual fix to the draft, surfaced at the Confirm): the
  catalogue direction of the 18 = 11 higher_better + 7 neutral (saves/passes/duels_won/defensive_actions/
  tackles/interceptions/blocks per90) + 0 lower_better. The draft's "all 18 higher_better / top always means
  good" is FALSE for the 7 neutral (volume/style) metrics; the honest read is "distributional position"
  (matches the CPO's "no good/bad colour"). The bar states WHERE the value sits, not a quality verdict.

decisions_reserved:
  - The GAP-21 export-wiring PR itself (analytics-engineer + cto + pytest) — the follow-up after this merges.
  - Any exact JSON nesting of benchmarks[] — confirmed at the wiring PR review (kept PROPOSED here).
  - The neutral-vs-higher_better wording nuance if the CPO wants it phrased differently than "distributional
    position" (surfaced at the Confirm).
  - Career screen, Phase C (#480), Phase D — un-picked backlog.
  - active_work.md handover refresh — a separate bookkeeping PR after this merges (not in this scope).

done_when:
  - docs/wireframes/12_player_stats.md reworked: ladder uses "median" (never "middle"); honest
    distributional-position framing for the 7 neutral metrics; all 18 metrics bound to real mart columns;
    the 5 ratio rows show the {num} of {den} · {pct}% triple; §10 registers GAP-21.
  - 03_player_profile.md: "Top scorers" restored + Stats link added. 00_overview.md: screen 12 + census
    updated. 99_gaps_register.md: GAP-21 added (with the num/den-atom requirement). metrics_display.md:
    "Percentile display (vs-peers)" section added with "median" + the distributional-position framing.
  - scope-auditor PASS + bi-analyst-reviewer PASS (>=2 named risks each); review.md diff_sha256 binds; CPO merges.

amendments: (none)
