# Review — feature/177-catalogue-order

diff_sha256: 57bfecc54b9523c9d5993465e8ef4e0f5a9ef1b26b6fe31da848a52c949535dd

rounds: 2

## scope-auditor
VERDICT: PASS
risks_checked:
- The impact map pastes the lineage: one model downstream of the catalogue (direction only), 57 tests; nothing in dbt reads metric_order but the seed's uniqueness test.
- Every path is in scope_paths; the three added paths carry a dated approved amendment.
- The order table matches decisions_taken; no new mechanism, cost or reserved decision.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- No (entity, group, metric_order) repeats; the uniqueness test still filters blanks.
- The export sorts only by catalogue fields and fails on a shown board without a place; the Form comparison keeps its 36 rows.
- The BL1 sample is a pure reorder; the docs state the export's selection rule.

## football-analytics-expert-reviewer
VERDICT: PASS
risks_checked:
- Only metric_order changes, on 23 rows; no other column moves.
- Each total sits after its per-match twin; player orders follow the team order of the same measure.
- Volume before rate, goals before assists, yellow before red.

## platform-reviewer
VERDICT: PASS
risks_checked:
- A fetch-level test runs the Rankings and leaderboards fetches through a faked warehouse and fails when the ordering is removed.
- _in_catalogue_order is a pure read and sort; no query, page or request changes.
- The Form comparison selection matches its pinned test.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- Every Rankings and Home board has a place; only the Passing player boards move, to Passes, Pass accuracy, Key passes.
- The committed BL1 sample and build show that order in EN, DE and FI; no other page's text changes.
- The edited metrics_display.md, 01_fixture_page.md and README sentences match the export.

## escalations
(none)
