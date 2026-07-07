# Task contract — #391 GAP-23: wire mart_team_competition_benchmarks into the team payload

> Written on a CLEAN tree (branch feat/391-gap23-team-benchmark-export off main @ bb368c0).
> Plan approved via ExitPlanMode this session. The #627-for-teams follow-up; flips the team-benchmark board green.

objective: >
  Wire the built-but-orphaned `mart_team_competition_benchmarks` into the v2 team export (`shape_team_payload`)
  as a per-season flat `benchmarks[]` block — the export analog of GAP-21/#627 for players, team-simplified (no
  position dimension, no num/den atoms). Select/reshape only (consumption-layer contract); the "k of N" /
  direction-mirror / spread-bar / LOCKED-16 render happens in the frontend, not here. This is the wiring that
  makes the team-benchmark row green on the content_architecture board; the spec is screen 14 (#664).
refs: #391 GAP-23; #664 (14_team_stats spec); #627/GAP-21 (player benchmark wiring — the pattern); mart_team_competition_benchmarks (built).

scope_paths:
  - scripts/export_site_data.py
  - tests/test_export_site_data.py
  - docs/content_architecture.md
  - docs/wireframes/**
  - .claude/task/**

impact_map: >
  writers: none — no model/mart touched. Consumption layer only (`scripts/export_site_data.py`).
  downstream: `fetch_team_payloads` reads `mart_team_competition_benchmarks` (grouped by team_sk, scoped on a
    sample run like mart_roster); `shape_team_payload` attaches a per-(league_code, season_api_year)
    `benchmarks[]` list via two NEW pure shapers (`_shape_team_benchmark_member`, `_shape_team_benchmarks`).
    Feeds the `teams` export entity (teams/*.json). Pure select/reshape — the shapers carry existing mart columns
    (metric_key, metric_value, rank, team_count, league_median/p25/p75, vs_median_delta), compute NOTHING (no
    ranking, no derivation, no direction verdict). Mirrors _shape_benchmark_member (player, #627).
  layer_rules: consumption-layer contract (layering.md) — verified the shapers only select existing values. All 20
    mart metric_keys are carried (no metric filtering — the frontend renders the LOCKED 16 per the display
    contract; filtering here would encode a display decision in the wrong layer, matching #627 which carried all rows).
  deploy_order: NON-breaking. Export-only; the next pipeline export run emits the enriched team payload. No dbt
    build, no --full-refresh.
  blast_radius: each team season row in teams/*.json gains a `benchmarks[]` list. No other entity changes; no
    number/metric moves; no data-build. content_architecture board team-benchmark row flips orphan → wired.

decisions_taken: >
  CPO-approved via the plan: mirror #627 team-simplified; flat benchmarks[] (no position nesting); carry the spec
  §5 columns; carry all 20 mart rows (frontend renders 16). Folding the directly-coupled doc-syncs (content_
  architecture board flip team-benchmark → green; 99_gaps_register GAP-23 → shipped; 14_team_stats banner/§10 →
  shipped) into this PR follows the GAP-01 precedent — the wiring is exactly what makes them true. No new metric,
  no derivation, no display decision in the export.

decisions_reserved:
  - The matchday-schedule board correction (a different §3 row, unrelated) — a separate follow-up.
  - Frontend rendering (the LOCKED-16 display contract) — not built.
  - A season_games_played mart column (games caption) — deferred (14 spec §10).

done_when:
  - `_shape_team_benchmark_member` + `_shape_team_benchmarks` added; `shape_team_payload` attaches per-season
    `benchmarks[]`; `fetch_team_payloads` fetches + passes the benchmark rows (scoped on sample runs).
  - Unit tests: member surfaces real columns (+ None-safe); flat byte-stable list; payload attaches per season.
  - `python -m pytest tests/test_export_site_data.py` green; python-ci green.
  - content_architecture §3/§7 team benchmark → ✓ wired; 99_gaps_register GAP-23 → shipped; 14 banner/§10 updated.
  - scope-auditor + analytics-engineer + cto + bi-analyst PASS (>=2 named risks each); review.md binds; CPO merges.

amendments: (none)
