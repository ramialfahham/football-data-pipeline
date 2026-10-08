# Review — feature/177-form-comparison-order — 2026-10-07

diff_sha256: 38b934f6e1a5a1eed741e7e84dad7b1572b46df25c122ffa86be09df70948073

rounds: 2

## scope-auditor
VERDICT: PASS
risks_checked:
- Every file is in scope_paths; the data README and the fixture wireframe join through a recorded doc-sync amendment.
- No new mechanism or recurring cost; metric_rows.json is an export file of the metric_groups.json kind, no BigQuery read.
- Reserved decisions untouched: team page, Rankings and Home rows; metricRows.ts changes only in a comment.
- The Form comparison only filters and keeps served order; a test blocks metric ids in the code it reads.
- Doc-sync: metric_rules.md, metric_layer.md, metrics_display.md, 01_fixture_page.md, the data README and the seed schema.

## bi-analyst-reviewer
VERDICT: PASS
risks_checked:
- All 36 served rows trace to catalogue rows and to mart_team_momentum columns; no field is fabricated.
- The components spell no metric id, order, direction or format.
- No naked percentage: every share has its count in the same group; dribbles_success_pct says "percentage".
- Discipline last; tier never orders; the team page keeps its 16 rows.
- 01_fixture_page.md §3c and metrics_display.md now describe the served rows.

## analytics-engineer-reviewer
VERDICT: PASS
risks_checked:
- The order lives in the seed; the export filters and copies; no model reads metric_order or metric_group_order.
- metric_order is 1..N per group, 36 team rows; metric_group_order 1..10; uniqueness test on (entity, group, order).
- The row set equals the mart_team_momentum metrics in metric_map.csv minus points_won.
- The guard test scans every file in the comparison's import closure; copy lines are skipped only in strings.ts.
- The per-match rule is one helper in the export.

## football-analytics-expert-reviewer
VERDICT: PASS
risks_checked:
- No description, formula, format, tier or direction changes; only metric_order and three group orders.
- Group order 1..10 with no gap or tie; Discipline last of the shown groups.
- The order inside each group reads sensibly to an analyst.

## platform-reviewer
VERDICT: PASS
risks_checked:
- The new export entity reads only the seed and runs in the default --entities set; CI's explicit entity lists skip it.
- tests/test_metric_rows.py fails on regeneration drift, set drift, order gaps and a wrong per-match flag.
- The guard self-checks cover the one-line and multi-line forms; the import follower fails closed.
- Pin tests only move down.

## escalations
(none)
