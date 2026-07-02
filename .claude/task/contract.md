# Task contract — GAP-21: wire mart_player_competition_benchmarks into the player export (#391)

> Written on a CLEAN tree (branch feat/391-gap21-benchmarks-export off main @ ebbcfd4).
> Code + mart change (scripts/export_*.py + dbt_project/models/** + a macro) — full plan mode + ExitPlanMode
> Confirm before implementing. The Stats-percentile screen (docs/wireframes/12_player_stats.md) is spec'd
> (#625); this wires its mart. See docs/working_agreement.md §1.

objective: >
  Wire mart_player_competition_benchmarks (built, LONG per (player, season, position_group, metric_key)) into
  the v2 player export so the Stats-percentile screen (12) has a payload — turning the benchmarks orphan mart
  → wired (the "cheap green", mirroring GAP-20 roster #619). Add a per-season benchmarks[] block to the player
  payload. For the 5 ratio metrics the display needs the volume triple {num} of {den} · {pct}% (no naked %),
  so the num/den atoms (which exist only in the 4_intermediate position-split model, NOT the mart) must reach
  a mart the export can read.

refs: >
  main @ ebbcfd4. Spec: docs/wireframes/12_player_stats.md §3/§5 + GAP-21 (99_gaps_register.md) + the
  Percentile-display section of metrics_display.md (all merged in #625). Pattern to mirror: GAP-20 squad
  wiring — scripts/export_site_data.py _shape_squad_member (135) + shape_team_payload squad[] (203-211) +
  fetch_team_payloads mart_roster query (470-478). Player side: shape_player_payload (243), fetch_player_
  payloads (485). Mart: mart_player_competition_benchmarks.sql; engine int_player_competition_benchmarks.sql;
  macro player_benchmark_metrics.sql; atoms in int_player_season_position__metrics.sql.

scope_paths:
  - dbt_project/models/5_marts/shared/mart_player_competition_benchmarks.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/macros/player_benchmark_metrics.sql
  - dbt_project/models/4_intermediate/shared/int_player_season_position__metrics.sql
  - scripts/export_site_data.py
  - tests/test_export_site_data.py
  - .claude/task/**

impact_map: >
  STRUCTURAL surfaces touched — impact mapped:
  - mart_player_competition_benchmarks (VIEW, LONG) gains 2 display columns: metric_numerator +
    metric_denominator — non-null ONLY for the 5 ratio metric rows (save_pct, pass_accuracy_pct,
    finishing_efficiency, dribbles_success_pct, duels_won_pct), null for the 13 per-90 rows. Sourced from the
    season CTE (int_player_season_position__metrics) atoms; a small +/- for save_pct (saves + goals_against)
    and finishing (goals - goals_penalty) is computed IN the mart (dbt), never the export.
  - player_benchmark_metrics() macro gains OPTIONAL num/den expression keys per ratio metric. The shared
    macro is also read by the engine (int_player_competition_benchmarks) which uses only key/col/pos/floor —
    extra keys are ignored, engine output unchanged. (Alternative considered: a mart-local mapping to avoid
    touching the shared macro — a plan decision.)
  - No new dbt MODEL; the benchmark mart is a leaf (only the export consumes it). It is a VIEW → no
    incremental full-refresh needed. No catalogue change (num/den are display atoms, not metrics — the drift
    guards check int_*_season__metrics, not this mart).
  - scripts/export_site_data.py: shape_player_payload gains a benchmark_rows param + a per-season benchmarks[]
    block; a _shape_benchmark_member helper; fetch_player_payloads queries the mart (scoped on sample runs).
    Selection/reshape only — no derivation (consumption-layer contract).
  - Downstream: the player payload JSON gains seasons[].benchmarks; no other consumer. CI: ci-data-build
    (dbt build + DQ) + python-ci (pytest) run.

decisions_taken: >
  Bind honestly to the merged spec (#625). Nothing here re-decides §10; the display rules are locked in
  12_player_stats.md + metrics_display.md. The build choices below are engineering placements presented for
  the Confirm (not silent):
  (1) The ratio num/den atoms reach the export via NEW columns on mart_player_competition_benchmarks (the
      export reads marts only; int_player_season_position__metrics is a 4_intermediate model + is position-
      split so mart_player_profile's whole-season atoms would be WRONG for multi-position players). This makes
      GAP-21 a mart + export change (analytics-engineer + cto), not export-only.
  (2) benchmarks[] nesting: per season, grouped by position_group, each with an ordered metrics[] list — the
      exact shape confirmed at this Confirm (§5 kept it PROPOSED).
  (3) Reuse the GAP-20 pattern (helper + per-season block + scoped fetch). Null/absent handling mirrors squad
      (omit rows the mart floor already excluded; byte-stable order).

decisions_reserved:
  - The three build choices above are put to the CPO at the ExitPlanMode Confirm — approve or redirect.
  - No frontend (Phase E) — this is data+export only.
  - Career screen, Phase C (#480), Phase D — still un-picked backlog.

done_when:
  - mart_player_competition_benchmarks carries metric_numerator/metric_denominator (ratio rows only), documented
    + DQ-tested in shared.yml. The player export attaches per-season benchmarks[] (position_group → metrics[])
    with the real mart columns incl. num/den for ratio metrics; no naked %.
  - Unit tests (tests/test_export_site_data.py) cover _shape_benchmark_member + the benchmarks[] attachment
    (incl. the ratio triple + a non-ratio row's null num/den).
  - scope-auditor + analytics-engineer + cto PASS (>=2 risks each); review.md diff_sha256 binds; ci-data-build
    + python-ci green; CPO merges.

amendments: >
  1 (CI-driven, 2026-07-02): ci-data-build failed to BUILD the mart — "Unrecognized name: goals_penalty".
  The finishing numerator `goals - goals_penalty` references `goals_penalty`, which
  int_player_season_position__metrics AGGREGATES (its aggregated CTE, `sum(goals_penalty) as goals_penalty`)
  but does NOT expose in its final SELECT (the other 4 ratios' atoms are all output columns; only this one was
  internal). Extend scope to add int_player_season_position__metrics.sql and surface `goals_penalty` as an
  output column — it is already summed; the macro num expr stays `goals - goals_penalty` (matches the
  wireframe §5). NOT a §10/product change: a data-availability fix that makes the already-approved finishing
  triple computable. The model is a table (non-incremental) → full rebuild, no NULL-out. It outputs many raw
  atoms already (goals/duels_total/…) so it is not the catalogue drift-guarded season-metrics model.
