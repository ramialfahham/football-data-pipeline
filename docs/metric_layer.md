# Metric layer

> Where each thing about a metric lives. Two rules live here: how a metric group is defined, and
> how provider facts and warehouse metrics stay apart. Every other rule is stated once, at its
> source, and shown in BigQuery on the table that carries it.

## Where each thing lives

| You need… | Go to |
|---|---|
| what a metric means, and its formula | `dbt_project/seeds/metric_catalogue.csv`: `description`; `base_relation`, `numerator_expr`, `denominator_expr` |
| how metrics are computed, and when a value is blank (rules R1 to R7) | the `metric_catalogue` doc block in `dbt_project/models/docs/metric_rules.md`, the catalogue table's description in BigQuery |
| how deserved points, the ranks, the contribution share and the league position are computed | each one's model description |
| who enters a ranking or a benchmark | the `ranking_rules` doc block in `dbt_project/models/docs/metric_rules.md`, on the ranking and benchmark tables |
| how the provider's values are cleaned | the `cleaning_rules` doc block in `dbt_project/models/docs/cleaning_rules.md`, on the two cleaned base tables |
| what each window holds | the `window_type__form` doc block in `dbt_project/models/docs/metric_rules.md`, on every `window_type` column of the form window; the `window_type__season_record` doc block in `dbt_project/models/docs/shared_columns.md`, on every `window_type` column of the season record |
| which window a match uses | `docs/metrics_context_model.md` section 4 |
| how a description is written | `dbt_project/docs/engineering_standards.md` section 2 |
| which model computes a metric on which surface | the surface list in `scripts/generate_metric_sql.py` |
| how a metric is shown: tier, row order, row patterns | `docs/wireframes/metrics_display.md` |
| what a metric is called on screen | the i18n layer; the catalogue holds `label_i18n_key` and `label_en` |
| what a test fails on | the test's own header in `dbt_project/tests/` |

## A group is defined once

A metric group is defined by three things and nowhere else: its **key**, the catalogue's
`metric_group` value on every metric it holds; its **order**, the catalogue's `metric_group_order`,
the same value on every row of the group and the positions 1..N across groups; and its **names**,
site copy keyed by the group key (`metricGroups.<key>.label` in `site_v2/src/i18n/strings.ts`,
one per language). The export publishes the key and order as `metric_groups.json`; every surface
that shows a group heading reads the groups from that file and the heading from the copy. No
document, seed or component spells a group's name or order on its own. Three checks hold it:
`assert_metric_group_order_is_one_per_group` in the warehouse, `tests/test_metric_groups.py` on
the committed export, and `site_v2/scripts/check-metric-labels.test.mjs` on the copy.

## Adding or changing a metric

1. Add the `metric_catalogue.csv` row. `description`, `direction` and `interpretation` are required —
   a row without them fails a guard, not a review.
2. Add it to the surface's list in `scripts/generate_metric_sql.py` and run
   `python scripts/generate_metric_sql.py`; the pytest in `test:python` fails when a model and the
   catalogue differ.
3. Run `python scripts/sync_metric_docs_blocks.py` and commit the result.
   `models/docs/metric_columns.md` is **generated** from the seed; hand-editing it fails CI
   (`--check` runs in `validate:governance`).
4. Keep the `description` inside BigQuery's 1,024-character column limit —
   `scripts/check_description_hygiene.py` measures the RENDERED text.
5. Add a 0–1 range test if it is a ratio.

## Facts from the provider, metrics from the warehouse

Which numbers are facts taken from the provider as published is rule R7 of the catalogue table's
description. The two never mix inside one block: a table is the provider's row, a board is
catalogue metrics. Where they overlap — the provider's points and the catalogue's `points_won`
tally — a reconciliation test guards the pair rather than one replacing the other.
