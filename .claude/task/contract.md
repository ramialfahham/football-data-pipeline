# Task contract — the metric map: where each catalogue metric can be read in the marts

objective: >
  How step 4 of the issue "Metric layer: every rule in one place, plain descriptions, a map an AI
  can read" (#190). scripts/sync_metric_docs_blocks.py generates a seed, metric_map, with one row
  per mart column that holds a catalogue metric: the table, the column, the metric, its variant
  (read from the column name) and, where the window or the metric varies by row, the column that
  says which. Every catalogue metric has a row, so the five season metrics no mart carried become
  columns of mart_team_season and mart_player_profile. A pytest checks 20 fan questions against
  the map. Mart columns that hold a catalogue metric but were described by hand point at the
  metric's block, so the map finds them; five team columns that showed a player's definition
  point at a team description instead.

refs: >
  #190, its checklist lines and How step 4 as edited on 2026-10-04 with the CPO's answers in chat
  that day. #190 steps 1 to 3 are merged (!243, !245, !246).

acceptance_criteria:
  # The issue's checklist lines this MR delivers, verbatim.
  - "A generated table in the warehouse, `metric_map`, maps every mart column that holds a catalogue metric (table, column) to its metric, its variant (this season, last season, change, home side, form) and, where the window varies by row, the column that says which. A long-format mart enters with one row per metric it holds: its value column, and `metric_key` as the column that says which metric. 20 fan questions, each with the table and column that answers it, are checked against it."
  - "Every catalogue metric has at least one mart column in the map: `goals_penalty`, `goals_own` and `goals_open_play` become columns of `mart_team_season`, and `goals_penalty_player` and `goals_open_play_player` of `mart_player_profile`."

scope_paths:
  - scripts/sync_metric_docs_blocks.py
  - tests/test_sync_metric_docs_blocks.py
  - tests/test_metric_map.py
  - dbt_project/seeds/metric_map.csv
  - dbt_project/seeds/schema.yml
  - dbt_project/models/docs/metric_columns.md
  - dbt_project/models/docs/shared_columns.md
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/models/5_marts/domestic_league/domestic_league.yml
  - dbt_project/models/5_marts/shared/mart_team_season.sql
  - dbt_project/models/5_marts/shared/mart_player_profile.sql
  - docs/metric_layer.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md
  - .claude/task/audit_reviewer_outputs.md
  - docs/tracker/**

impact_map: >
  writers: mart_team_season and mart_player_profile are each written only by their own model;
  metric_map is a new seed, written by dbt seed from the generated CSV.
  downstream, `dbt ls --project-dir dbt_project --select mart_team_season+ mart_player_profile+
  --resource-type model`: mart_player_profile, mart_team_profile, mart_team_season,
  mart_team_season_insights. mart_team_profile and mart_team_season_insights select named columns
  from mart_team_season (ts.played ... ts.latest_form), so the three new columns do not reach
  them. Consumption: scripts/export_site_data.py reads mart_player_profile with select * and copies
  each season row into the player payload, so the two new player columns reach the player page
  data; no file under site_v2/src names them. metric_map has no reader.
  layer_rules: the two marts read the season intermediates they already read
  (int_team_season__metrics, int_player_season__metrics); no new ref, no partition_by or
  cluster_by; check_layer_contract.py unchanged.
  deploy_order: additive. Prod gains the columns and the seed on the first build after the merge
  (the post-merge data:build:main, else the 04:00 nightly); nothing reads them before.
  blast_radius: no existing value changes; the two marts gain five columns. The description of
  29 mart columns changes in BigQuery (persist_docs): 24 point at their metric's block, 5 at a
  team description. Measured offline: 346 mart columns reference a metric block today, 65 metric
  rows come from the four long-format marts, and 5 catalogue metrics reach no mart.

decisions_taken: >
  The CPO's answers in chat on 2026-10-04, to the five questions of #190 step 4: the table name
  "metric_map (Recommended)"; the scope "Marts only (Recommended)"; the long-format marts "One row
  per metric (Recommended)"; the five metrics no mart carries "Add them to marts (Recommended)";
  the 20 fan questions "Approve as listed (Recommended)". #190 records them.

  Readings, under the CPO's delegation in chat on 2026-10-02 ("Readings of approved rules are
  yours; apply the most plausible one and state it in one line"):
  - The map is a seed CSV the script writes beside metric_columns.md, as sync_dbt_vars.py writes
    competition_registry.csv; --check, already in validate:governance, fails on drift, on a
    catalogue metric with no mart row and on a long-format mart it cannot read.
  - The map holds placement only: table_name, column_name, metric_id, variant, window_column,
    metric_key_column. The entity is the catalogue's, joined by metric_id, which is unique.
  - The variant is read from the column name's affixes: empty for the metric over the table's
    row; this_season, prev_season, prev_season_full, delta_yoy, sum_season; home, away, opponent,
    last_meeting, recent_meetings; form for a form-window column; a side and a period join with
    an underscore (home_form).
  - window_column names window_type where the table has it. mart_matchday_insights keeps only a
    qualifiers flag, so its form columns carry the variant home_form or away_form and no window
    column.
  - A mart column holds a catalogue metric when its value is that metric's formula, or for
    league_rank its source, over the table's row, a window, a side, the opponent or a season
    total. Such a column points at the metric's block; one that holds none points at none. A
    count the catalogue does not define (a team's shots, passes, offsides), a value scaled to a
    whole percentage, a provider's table points or goals, and a count of results are not metric
    columns.
  - A hand-written block left with no reference is deleted.
  - The 20 questions are a pytest's cases, read against the committed CSV, not a warehouse table.

  Threshold declarations. NEW MECHANISM: none; a generated seed with a drift check is the
  competition_registry.csv pattern, and the new checks run inside the existing script and its CI
  step. RECURRING COST: the seed loads with the nightly seed run and carries five tests (not_null
  on its three key columns, their uniqueness, and metric_id's relationship to the catalogue) on
  tables under 1 MB, each billed at BigQuery's 10 MB minimum, about 50 MB a night; the two marts
  gain five integer columns.

decisions_reserved:
  - Metric ids, names, labels, formulas and the catalogue's rows are unchanged (#177, #94).
  - The same player definitions on team stat columns in fct_fixture_team_stats and
    int_legs__team_match are outside marts-only scope; they go to their own issue.
  - No existing value changes.

done_when:
  - python scripts/sync_metric_docs_blocks.py --check passes on the real repo, and the map has a
    row for every catalogue metric.
  - pytest on tests/test_sync_metric_docs_blocks.py and tests/test_metric_map.py passes; each new
    check is shown red on a deliberate break.
  - check_description_hygiene.py, check_relationships_coverage.py, dbt parse, sqlfluff on the two
    changed SQL files and ruff pass.
  - The review cycle passes with every routed reviewer, review.md bound to --staged-hash.
  - data:build:mr is green; its build of the two marts is compared with prod (bytes to the CPO
    first): existing columns equal, the new columns equal the season intermediates.

amendments: (none)
