# Task contract — Statistics pages, step 1a: the catalogue order of two goals metrics

objective: >
  Issue #347 (build of the Statistics pages; design approved on #139 and #140), step 1 of its
  How, first of two merge requests. Two catalogue rows, goals_penalty_player and
  contribution_player_pct, have no metric_order; they take the end of the Goals group (7 and 8),
  decided in chat and recorded in decisions_taken, so the Statistics leaderboard pages list them
  in the catalogue's order. The export of the full ranked field is the second merge request.

refs: >
  #347; #139 approved design and notes of 2026-11-10 and 2026-11-12; #140.

scope_paths:
  - dbt_project/seeds/metric_catalogue.csv
  - tests/test_catalogue_order.py
  - .claude/task/347-statistics-export/contract.md
  - .claude/task/347-statistics-export/review.md
  - .claude/task/347-statistics-export/review_input.patch

depends_on:
  - none: the only open MRs share no file with these two

shared_files:
  - none: no design baseline, chart manifest or chart pin changes

approved_design:
  - statistics: #139

impact_map: >
  writers: no ingestion or dbt model changes. The one seed edited, metric_catalogue, is read by
  the marts only for direction and format.
  downstream: `dbt ls --select metric_catalogue+ --resource-type model` returns
  mart_leaderboards, mart_player_competition_benchmarks, mart_team_competition_benchmarks and
  mart_team_leaderboards. None reads `metric_order`; the two metrics that gain a place
  (goals_penalty_player, contribution_player_pct) are read by mart_leaderboards for direction and
  format, which do not change. Consumption of metric_order: scripts/export_site_data.py, which
  orders the boards by it; neither metric is in a board set the export serves today, so no
  payload changes in this MR (the fetch_metric_rows and fetch_player_metric_rows row sets are
  filters that also require a metric_order and are pinned by
  tests/test_form_comparison_metric_set.py).
  layer_rules: check_layer_contract.py does not apply (no model changes); the seed's change is
  checked by tests/test_catalogue_order.py.
  deploy_order: additive. The two new metric_order values reach the warehouse with the next seed
  load and change no mart column.
  blast_radius: none. No page output and no payload changes in this MR.

decisions_taken: >
  The two catalogue rows without a place take the end of the Goals group, penalty goals 7 and
  share of team goals 8, after the metrics #139 names in its forms list (approved in chat,
  2026-11-23).

decisions_reserved:
  - none: every rule applied is named in decisions_taken with its approval

done_when:
  - full pytest passes
  - tests/test_catalogue_order.py pins the two places
