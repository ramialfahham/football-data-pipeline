# Task contract — #177, part 3: the Form comparison takes its rows from the catalogue

objective: >
  The match page's Form comparison shows the approved 36-metric list, grouped and ordered as the
  catalogue says, from a file the export writes from the catalogue; no site file lists the rows.
  The catalogue gains metric_order (the order within a group) and Discipline becomes the last group.

refs: >
  #177 (the metric catalogue): the catalogue holds the order within a group, every surface only
  filters, Discipline last everywhere; #166 "Form comparison rows" (the 36-metric list); the column
  name metric_order and the acceptance criteria approved in chat, 2026-10-07; the names of the new
  metrics approved in chat, 2026-10-07.

acceptance_criteria:
  - The Form comparison shows the rows of the approved 36-metric list that the match's data carries, grouped and ordered as the catalogue says; no site file lists them.
  - Every surface that shows metric groups puts Discipline last.
  - A test fails when the Form comparison, or anything it reads in site_v2/src, spells a metric's key, order, direction or format.
  - The team page shows the same rows as today, in the new group order.

scope_paths:
  - dbt_project/seeds/metric_catalogue.csv
  - dbt_project/seeds/schema.yml
  - dbt_project/models/docs/metric_rules.md
  - dbt_project/models/docs/metric_columns.md
  - dbt_project/seeds/metric_map.csv
  - scripts/export_site_data.py
  - tests/test_metric_groups.py
  - tests/test_metric_rows.py
  - tests/test_sentence_length_in_docs.py
  - tests/test_no_decision_history_in_docs.py
  - site_v2/src/data/metric_groups.json
  - site_v2/src/data/metric_rows.json
  - site_v2/src/i18n/strings.ts
  - site_v2/src/lib/metricRows.ts
  - site_v2/src/lib/types.ts
  - site_v2/src/components/fixture/MetricComparison.astro
  - site_v2/src/components/fixture/MetricRow.astro
  - site_v2/scripts/check-metric-labels.test.mjs
  - docs/metric_layer.md
  - docs/wireframes/metrics_display.md
  - docs/wireframes/01_fixture_page.md
  - site_v2/src/data/README.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md
  - .claude/task/audit_reviewer_outputs.md

impact_map: >
  writers: metric_catalogue.csv by hand; metric_groups.json and metric_rows.json by the export from
    the catalogue (no BigQuery read). No dbt model changes.
  downstream: the seed gains one column and three groups change their metric_group_order
    (goalkeeping 7→6, set_pieces 8→7, discipline 6→8). Readers of metric_group_order: the export's
    metric_groups.json (every surface's group order: Form comparison, team page, Rankings) and the
    singular test assert_metric_group_order_is_one_per_group; no model reads it (`grep -rn
    metric_group_order dbt_project/models` → none). metric_order is new; its only reader is the
    export's metric_rows.json, read by MetricComparison.astro.
  layer_rules: the catalogue defines; the export selects and copies; the site renders served order.
  deploy_order: the seed rebuilds with the nightly; the site changes on the next manual deploy.
  blast_radius: the group order on every surface; the Form comparison's rows (the approved list the
    payload carries). No number changes.

decisions_taken: >
  The column name, the acceptance criteria and the metric names are approved in chat, 2026-10-07.
  The group order follows #177 / #166 (Discipline last everywhere). The Form comparison shows the
  team metrics with a metric_order; tests/test_metric_rows.py holds that set equal to the metrics
  metric_map.csv places in mart_team_momentum, minus the Results group (points_won). Per match is
  the catalogue's fact (denominator count(*) and not a share). The team page keeps metricRows.ts
  until its own MR.

  THRESHOLD DECLARATIONS: NEW MECHANISM: none (an export file of the metric_groups.json kind).
  RECURRING COST: none.

decisions_reserved:
  - The team page, Rankings and Home rows from the catalogue: their own #177 MRs.

done_when:
  - pytest tests/ passes; npm test passes; check_copy_gate passes; dbt parse clean.
  - astro build of the committed sample; the built match pages show the approved rows in the
    catalogue's order, Discipline last; the team page shows its 16 rows in the new group order.

amendments:
  - Review round 1 adds docs/wireframes/01_fixture_page.md and site_v2/src/data/README.md to scope_paths. Both
    describe what this change alters (the Form comparison's rows, the export-written data files), so the
    doc-sync rule requires them in the same MR. No new decision.
