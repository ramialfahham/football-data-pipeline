# Review — feat/metric-layer-phase1 — 2026-06-18

> Machine-checked review artifact (G3, step 4 Lock). Reviewers required by .claude/review_routing.json
> for the changed paths: scope-auditor (always), analytics-engineer-reviewer (dbt_project/**),
> football-analytics-expert-reviewer (metric_catalogue.csv). All PASS; no FAIL; no ESCALATE.

diff_sha256: 73ac4b641ed4cfc54eafe7220ec144c13dac1130f295e58c7ff2b0b5bceb5e73

## scope-auditor
VERDICT: PASS
risks_checked:
- Scope + over-build removal: all 5 changed files are within scope_paths; confirmed NO leftover binding-map seed, metric_kind column, or context flag (the reverted over-build); decisions_reserved respected — no model SQL changes, no recompute/conformance engine.
- Drift-test normalisation soundness: the two normalisations (strip `_season`; map `goals_saves`->`saves`) handle the known naming gaps only; a new or unregistered metric column is still caught -> the no-drift guarantee holds.
- i18n follow-up (non-blocking): the 4 new label_i18n_keys are not yet in site/i18n, so a glossary tooltip renders blank until added — NOT a contract violation (contract = cataloguing only) and does not fail CI (not manifest metrics). Flagged as a follow-up.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- Drift-test coverage (no false positive / negative): traced every output column of both season models; the `*_sum_season` intermediates, `*_sk` keys, coverage counts and playing-time facts are correctly exempt; the player-derived sums are not output columns; after the 4 catalogue additions every non-exempt column maps to a catalogue (entity, metric_id) — the test returns zero rows (passes now) and WOULD FAIL on a future uncatalogued metric.
- Parse-safety + DAG ordering: the `{% if execute %}` guard suppresses the adapter call at parse; the `-- depends_on:` directives sit after the `#}` comment and before the Jinja (the correct dbt position for ref()-in-conditional); test-paths includes tests/. `finishing_efficiency` is correctly EXCLUDED from the 0-1 range test (uncapped); the new player ratio columns are genuinely bounded 0-1.

## football-analytics-expert-reviewer
VERDICT: PASS
risks_checked:
- shot_share: numerator shots_total / denominator (shots_total + opponent_shots_total); the model uses nullif on the denominator so it is NULL when no shots (matches the description); a share is always in [0,1] (no capping needed); lower_is_better=false is correct.
- points_capture: points_won / (3 * games); the denominator is always positive (a season row implies >= 1 game), so no null / divide-by-zero; bounded [0,1] by construction (no "exceeds 100%" caveat, unlike finishing_efficiency); description consistent.
- goals_conceded / shots_total consistency: goals_conceded is the atomic constituent already used by save_pct + shots_on_target_faced (not a duplicate — now exposed as a standalone count; matches metrics_display "defined but unrendered"); player shots_total collides with no team usage (entity discriminator); lower_is_better=true on goals_conceded is correct.

## escalations
(none)
