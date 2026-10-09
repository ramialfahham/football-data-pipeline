# Task contract — #177 part 3: one order for every metric, from the catalogue

objective: >
  Every metric a surface shows has its place in its group in the catalogue's metric_order. The export
  orders the Rankings and Home boards by the catalogue and only filters with its board lists; the Form
  comparison keeps its rows. The docs say the order is the catalogue's.

refs: >
  #177 ("the catalogue holds the order of the metrics within a group ... every surface shows its metrics
  in that order and only filters"), decided on #132. The plan, the order table, its readings and the
  acceptance criteria: approved in chat, 2026-10-09.

scope_paths:
  - dbt_project/seeds/metric_catalogue.csv
  - dbt_project/seeds/schema.yml
  - scripts/export_site_data.py
  - tests/test_metric_rows.py
  - tests/test_export_site_data.py
  - tests/test_catalogue_order.py
  - site_v2/src/data/metric_rows.json
  - docs/metric_layer.md
  - docs/wireframes/metrics_display.md
  - docs/wireframes/01_fixture_page.md
  - site_v2/src/data/README.md
  - site_v2/src/data/competitions/BL1/2026.json
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md
  - .claude/task/audit_reviewer_outputs.md

impact_map: >
  writers: metric_catalogue.csv by hand (metric_order only); the export writes metric_rows.json,
    metric_groups.json and the competition and landing payloads.
  downstream: `dbt ls --select metric_catalogue+ --resource-type model` returns one model,
    5_marts.shared.mart_team_leaderboards, which reads only `direction`; the same selection with
    `--resource-type test` returns 57 tests. `grep -rl "ref('metric_catalogue')" dbt_project/models`
    returns that one model; 24 other model files name the catalogue in comments or descriptions only.
    `grep -rl metric_order dbt_project/models dbt_project/tests dbt_project/macros` returns nothing; in
    dbt only seeds/schema.yml's uniqueness test on (entity, metric_group, metric_order) reads it. The
    export's readers of metric_order: fetch_metric_rows (Form comparison) and the board sorting for the
    Rankings, Home and leaderboards payloads. The site renders the served order. The committed BL1
    sample's two board lists are re-sorted by the export's order, no value changed.
  layer_rules: the catalogue holds the order; the export sorts by it and filters with its board lists;
    the site renders.
  deploy_order: the seed loads with the nightly; the export writes the new order; the site changes on
    the next manual deploy.
  blast_radius: the Rankings' Passing player boards (passes, pass accuracy, key passes); no other
    surface's order moves.

acceptance_criteria:
  - Every metric shown by the Rankings tab, Home or the Form comparison has a catalogue metric_order, unique in its entity and group.
  - On a built Rankings page the boards of each group follow the catalogue order; the Passing player boards read Passes, Pass accuracy, Key passes in EN, DE and FI.
  - Home's boards and the Form comparison rows show the same metrics in the same order as main's build.
  - Every page other than the Rankings tab shows the same text as main's build.

decisions_taken: >
  The plan, the order table (team: Shots on target difference 4 in Shooting, the rest after it one
  down; Yellow cards 4 and Red cards 6 in Discipline, per match 3 and 5; player: Goals 1, Assists 2;
  Shots on target 1, Goals per shot on target 2; Passes 1, Pass accuracy 2, Key passes 3; Dribbles
  attempted 1, Duels 2; Defensive actions 1; Saves 1; Yellow cards 1, Red cards 2), its readings and
  the acceptance criteria: approved in chat, 2026-10-09. Readings: a player metric takes the team order
  of the same measure; a total sits right after its per-match twin; a metric no surface shows keeps a
  blank order. The metrics_display.md sentence and the metric_layer.md order row, exact text:
  approved in chat, 2026-10-09.

  THRESHOLD DECLARATIONS: NEW MECHANISM: none. RECURRING COST: none; no query changes.

decisions_reserved:
  - Direction and format from the catalogue, the site's own copies (metricRows.ts) and the team page's
    order, the export reading the catalogue from the warehouse, the spelled-key checks: the next #177 MR.

done_when:
  - dbt parse clean; pytest tests/, npm test, npm run build (audit-seo, check-built-pages), the copy
    gate and check_design_inventory.py pass.
  - The acceptance criteria are shown in .claude/task/acceptance_evidence.md.

amendments:
  - 01_fixture_page.md's Metric rows sentence and site_v2/src/data/README.md's metric_rows.json sentence state the Form comparison's selection rule (the team metrics mart_team_momentum serves outside Results), exact text; the committed BL1 sample's board lists re-sorted by the export's order: approved in chat, 2026-10-09.
