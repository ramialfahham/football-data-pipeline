# Review — feat/391-gap23-team-benchmark-export — 2026-07-07

> G3 Lock artifact. #391 GAP-23 — wire `mart_team_competition_benchmarks` into the v2 team export
> (`shape_team_payload`) as a per-season flat `benchmarks[]` block (the #627-for-teams analog,
> team-simplified: no position nesting, no num/den atoms). Two new pure shapers + a `benchmark_rows` param
> + a scoped fetch (like mart_roster). Pure select/reshape (all 20 mart rows carried; frontend renders the
> LOCKED 16). + 4 unit tests + the directly-coupled board/doc flips (content_architecture team benchmark
> orphan → wired, 18 marts; 99_gaps_register GAP-23 → shipped; 14_team_stats banner/§10 → shipped). This is
> the wiring that flips the team-benchmark board row green. Required set (routing): scope-auditor + analytics-
> engineer + cto (scripts/export_*.py + tests/**) + bi-analyst (docs/wireframes/**).

diff_sha256: e80bf7f8b55cc3afcc922934331e57a6ee90c7d07e23c3baf1d1abf9a16db03b

## scope-auditor
VERDICT: PASS
risks_checked:
- **Consumption-layer boundary (all-20 vs LOCKED-16).** The export carries every mart row it receives with no
  filtering; the two shapers only select/reshape 8 existing columns — no rank, no direction verdict, no derivation.
  If mart coverage ever narrowed below 20 the export passes it through honestly (a mart-DQ boundary, not an export
  violation). §10: mirrors the approved #627 + GAP-20 precedent; no new metric/mechanism/display decision.
- **Sample-run team_sk scoping + board honesty.** The bench fetch mirrors the roster pattern (GAP-20 precedent),
  handles empty result-sets (empty `benchmarks[]` per wireframe §6), and the content_architecture flip (team
  benchmark → ✓ wired, 17→18 marts, no orphans) is TRUE given this wiring actually ships it (the query + pass-through
  are in the diff). Scope: all 6 staged files within scope_paths.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- **Field existence.** All 8 carried columns + the (league_code, season_api_year) grouping key + the team_sk fetch
  key are real, schema-tested columns of `mart_team_competition_benchmarks` (shared.yml, mart SQL) — no phantom field.
- **Sample-scoping NameError.** `id_list` is computed fresh inside the bench block's own `if sample:` branch,
  mirroring the fixtures/roster blocks — no cross-branch leak, no crash on a non-sample run.
- **Consumption-layer.** Both shapers are pure `.get()` passthroughs — no arithmetic/rank/derivation/direction;
  matches layering.md and the merged #627 precedent.
- **Metric-filtering / grain.** No filtering in `_shape_team_benchmarks` (all 20 metric_keys pass through); the mart
  has no `position_group` column, so the flat (non-nested) shape is grain-correct, not an omission.

## cto-reviewer
VERDICT: PASS
risks_checked:
- **`id_list` reuse.** Each of the three `if sample:` blocks recomputes id_list independently from the unchanged
  team_ids — no NameError, no stale-value bug.
- **Signature / call-site.** `benchmark_rows` is appended last with a None default; the one production call site
  (fetch_team_payloads → 4 positional args) + 7 test sites all valid; fetch_team_payloads' own signature unchanged.
- **Test soundness.** The new tests are pure (no BigQuery), assert real behavior (byte-stable order, per-season
  routing, internal-key exclusion, empty default), unique names, CI-collected (`pytest tests/ -v`, 32 passed).
- **Serialization + scope.** The 8 fields are str/float/int/None — serialize via the existing json.dumps(default=str);
  the diff touches exactly the 6 scope_paths files, no guard/CI/dependency surface.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- **§5 binding fidelity.** The 8 columns 14 §5 binds match `_shape_team_benchmark_member` EXACTLY (no more, no less;
  internal keys + league_mean correctly dropped); a unit test locks it in. The "shipped" claims in the 14 banner/§10
  + the gaps-register row are truthful.
- **"All 20 carried, frontend renders 16" + board honesty.** Traced end-to-end: the UNPIVOT lists 20 metric_keys,
  the export path has NO metric filter, so all 20 are carried; the 16 rendered in 14 §5 match metrics_display's
  LOCKED 16-row team table exactly (order + no tier disturbance); the no-num/den-for-teams claim matches the
  pre-existing LOCKED rule (metrics_display "team comparisons keep single % values — adjacent count rows provide the
  volume"). Enumerated the export's mart references post-patch = 18 distinct marts → "18 marts" is accurate.

## escalations
- None open. No ESCALATE. Pure consumption-layer wiring (mirrors #627/GAP-20); the board/doc flips are directly
  coupled to the shipped wiring (GAP-01 fold precedent). No new metric, derivation, or display decision in the export.
