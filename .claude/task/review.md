# Review — feat/metric-direction-semantics — 2026-06-19

> PR-a of the team competition-benchmark build: add `direction` (higher_better / lower_better / neutral)
> + `interpretation` columns to metric_catalogue, classify the 24 team metrics, document them in
> seeds/schema.yml. The semantic precursor to mart_competition_benchmarks__team (PR-b). dribbles_success_pct,team
> left unclassified (retiring → #510); player metrics deferred (v1.x); lower_is_better retained.
> Required reviewers for the staged paths (metric_catalogue.csv → analytics-engineer + football-analytics;
> dbt_project/** → analytics-engineer; always → scope-auditor) — all PASS.

diff_sha256: f2b049d2f3f7aa7fac5964037b37d56a8a4308e92896394ea3e4f64862353234

## scope-auditor
VERDICT: PASS
risks_checked:
- Catalogue positional-reader fragility: two new columns appended after group_display_order; a consumer using positional indexing would misread. Control held — the export uses csv.DictReader (by name, confirmed line 667), dbt seed/parse validates the columns, no row added/deleted, lower_is_better retained at its original position.
- Scope + no silent §10: all three files within scope_paths (no model/mart/export touched); the team classification (14 higher_better / 2 lower_better / 8 neutral) matches the CPO-agreed list quoted verbatim in the contract, incl. the corners→neutral reclassification and shots_per_match=higher_better; player rows empty (v1.x) and dribbles_success_pct,team untouched (#510) — deferred scope kept out, benchmark mart reserved to PR-b.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- accepted_values null-tolerance on direction: dbt's built-in accepted_values skips nulls, and direction carries no not_null, so the 31 player rows + dribbles_success_pct,team (empty direction) pass without a null guard — correct dbt behaviour, no test break. CSV integrity confirmed (all 56 lines = 13 fields; quoted comma-bearing descriptions intact; no row added/deleted; existing columns unshifted).
- corners_conceded_per_match lower_is_better/direction divergence: the row keeps lower_is_better=true alongside direction=neutral (the CPO reclassification); neither column constrains the other so no seed test fails; the divergence is intentional/documented (direction supersedes; lower_is_better retained for back-compat) and both flow independently via csv.DictReader by name. assert_metric_catalogue_unique_by_entity + the no-drift guard unaffected.

## football-analytics-expert-reviewer
VERDICT: PASS
risks_checked:
- shots_per_match = higher_better could read as a quality signal in isolation; mitigated — the interpretation says "high-volume but not necessarily high-quality" and the display funnel pairs it with danger_zone_ratio + shots_on_target; classification honest and contextualised.
- defensive_actions/tackles/interceptions/blocks/duels/passes classified neutral rather than higher_better is football-correct: high counts arise from opposite tactical shapes (deep block under pressure vs aggressive press / possession vs direct style), so a higher_better label would mislead; the interpretations describe the count without asserting good/bad, and defensive_actions explicitly names the "deep block OR aggressive press" ambiguity.
- corners_conceded reclassification from lower_better to neutral is sound (corner-to-goal conversion ~2-3% = low-information event); shot_share / points_capture remain transparent ratio formulas with no fabricated index; no new metric definitions added — only semantic metadata on existing rows.

## escalations
(none)
