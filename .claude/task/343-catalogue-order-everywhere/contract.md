# Task contract — The catalogue sets the metric order on every surface

objective: >
  Issue #343: `metric_order` in dbt_project/seeds/metric_catalogue.csv is the one place that orders
  metrics. Two corrections to it (Team Shooting; the combined player Cards metric leaves the order),
  tests that pin the order per group, that make players and teams read the same, and that fail when
  a surface shows another order; every surface and mock generator that orders metrics by anything
  else reads the catalogue; the team table in docs/wireframes/metrics_display.md follows it.

refs: >
  #343; #139 "Catalogue changes" (merged order, !431); the coordinating session's brief.

scope_paths:
  - dbt_project/seeds/metric_catalogue.csv
  - dbt_project/seeds/metric_map.csv
  - tests/test_catalogue_order.py
  - tests/test_metric_rows.py
  - tests/test_form_comparison_metric_set.py
  - tests/test_export_site_data.py
  - tests/test_export_landing.py
  - tests/test_leaderboard_board_sets.py
  - tests/test_design_mocks_read_catalogue_order.py
  - scripts/export_site_data.py
  - design-mocks/gen_*.py
  - design-mocks/check_*.py
  - design-mocks/catalogue_order.py
  - docs/wireframes/metrics_display.md
  - docs/metric_layer.md
  - docs/wireframes/14_team_stats.md
  - docs/wireframes/12_player_stats.md
  - docs/wireframes/03_player_profile.md
  - tests/test_no_decision_history_in_code.py
  - tests/test_no_decision_history_in_docs.py
  - tests/test_sentence_length_in_docs.py
  - site_v2/src/data/metric_rows.json
  - site_v2/src/data/player_metric_rows.json
  - .claude/task/343-catalogue-order-everywhere/contract.md
  - .claude/task/343-catalogue-order-everywhere/review.md
  - .claude/task/343-catalogue-order-everywhere/review_input.patch
  - .claude/task/343-catalogue-order-everywhere/acceptance_evidence.md

impact_map: >
  writers: none. metric_catalogue is a seed; its only writer is the seed file. The only column
  changed is metric_order, which no dbt model reads (`grep -rn metric_order dbt_project/models
  dbt_project/macros dbt_project/tests scripts/generate_metric_sql.py` finds one prose line in
  dbt_project/models/docs/metric_rules.md).
  downstream: `dbt ls --select metric_catalogue+ --resource-type model --resource-type seed
  --output name` returns exactly: mart_leaderboards, mart_player_competition_benchmarks,
  mart_team_competition_benchmarks, mart_team_leaderboards, metric_catalogue (5 nodes; 165 with
  their tests). `grep -rln metric_order dbt_project scripts/generate_metric_sql.py` returns
  dbt_project/models/docs/metric_rules.md, dbt_project/seeds/metric_catalogue.csv and
  dbt_project/seeds/schema.yml, so no model selects or sorts by metric_order and no mart value, row
  or column changes. The consumers of metric_order are scripts/export_site_data.py
  (`_in_catalogue_order`, `fetch_metric_rows`, `fetch_player_metric_rows`) and the design-mocks
  generators.
  layer_rules: check_layer_contract.py is unaffected (no model file changes); the seed's unique
  test on (entity, metric_group, metric_order) where metric_order is not null still holds, since
  the new Team Shooting values 1-12 are each used once and cards_player's value is cleared.
  deploy_order: independent of the nightly; the seed rebuilds in the next dbt run and nothing reads
  the changed column in the warehouse.
  blast_radius: the committed site_v2/src/data/metric_rows.json reorders in Shooting (shots on
  target against moves from last to third); player_metric_rows.json holds neither cards_player nor
  a team Shooting metric, so it does not change. Rankings and Home already read the catalogue and
  keep their order. cards_player stays a mart column and a Leaderboards payload field; it only
  leaves the order.

approved_design:
  - match: #132
  - team: #134

acceptance_criteria:
  - site_v2/src/data/metric_rows.json lists the same 34 metrics as on main; in Shooting, shots on target against sits after shots on target and before shots inside box per match.
  - site_v2/src/data/player_metric_rows.json is unchanged.
  - No other file under site_v2/src changes.

depends_on:
  - none: the catalogue's order is on main; no open MR changes metric_catalogue.csv or the surfaces (!256 is on hold and makes no order change)
shared_files:
  - none: no design baseline, component registry, font coverage or chart screenshot file changes; the chart screenshot check reports 0 differences over 18 screenshots

decisions_taken: >
  The order is the one on main (the Statistics review's catalogue changes, #139, merged in !431),
  with the two corrections #343 lists in its first checkbox (the issue is the request; the CPO
  said the order is never asked again). The Team Shooting order is the one #343 lists. cards_player
  gets no metric_order, so players and teams both show yellow cards and red cards. The remaining
  metric_order values stay as they are, including the gaps that team Discipline and player
  Discipline already carry. Each surface that held an order of its own now reads the catalogue's; no
  surface gains or loses a metric. Shots off target and blocked shots take places 11 and 12 as
  #343 lists them. A place never decides whether a page shows a metric: the export's Form comparison
  and player comparison rows come from the named sets `_FORM_COMPARISON_METRICS` and
  `_PLAYER_COMPARISON_METRICS`, which the pin tests hold, so the two new places add no row to the
  approved match and team pages. The played-match mock (gen_match_page) draws its stat rows in the
  catalogue's order.

decisions_reserved:
  - none: every rule applied is named in decisions_taken and is the one #343 states

done_when:
  - python -m pytest tests/test_catalogue_order.py tests/test_metric_rows.py tests/test_form_comparison_metric_set.py tests/test_design_mocks_read_catalogue_order.py -q passes
  - python scripts/ci_local.py --mr passes
  - full pytest passes

amendments: (none)
