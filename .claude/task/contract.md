# Task contract — retire mart_team_fixture_stats and the old match-stats export

objective: >
  mart_team_fixture_stats, a raw copy of the provider's team stat line, is removed, and with it
  the old matchstats export that no site component reads. A played match's team numbers come from
  mart_team_window_metrics' window of one. The form list's has_team_stats flag reads that window
  instead, so it still says whether the played match's page holds a team stat line. No page and no
  payload the site reads changes.

refs: >
  #176 (https://gitlab.com/rami.al-fahham/football-data-pipeline/-/work_items/176), the line
  "mart_team_fixture_stats is removed once nothing reads it (with the old match-stats export)".
  The plan and the document texts in decisions_taken: approved in chat, 2026-10-14.

scope_paths:
  - dbt_project/models/5_marts/shared/mart_team_fixture_stats.sql
  - dbt_project/models/5_marts/shared/mart_team_momentum_window.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/tests/assert_team_metrics_follow_catalogue_formula.sql
  - dbt_project/seeds/metric_map.csv
  - dbt_project/models/docs/metric_columns.md
  - dbt_project/docs/layering.md
  - scripts/export_site_data.py
  - scripts/generate_metric_sql.py
  - tests/test_export_site_data.py
  - tests/test_metric_map.py
  - tests/test_no_decision_history_in_code.py
  - tests/test_no_decision_history_in_docs.py
  - tests/test_sentence_length_in_docs.py
  - docs/content_architecture.md
  - docs/site_architecture.md
  - docs/wireframes/01_fixture_page.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md

impact_map: >
  writers: dbt builds mart_team_fixture_stats from fct_fixture_team_stats; nothing else writes it.
  downstream: pasted output of `dbt ls --select mart_team_fixture_stats+ --output name` on the
  branch's base (dbt 1.7.20): the models mart_team_fixture_stats and mart_team_momentum_window;
  the singular tests assert_momentum_window_matches_momentum,
  assert_team_metrics_follow_catalogue_formula and assert_tournament_form_window; and the generic
  tests of those two models, among them not_null_mart_team_momentum_window_has_team_stats and
  team_fixture_stats_passes_accuracy_percent_in_range. Outside dbt:
  scripts/export_site_data.py (fetch_matchstats_payloads, shape_matchstats, the matchstats
  entity; fetch_fixture_payloads passes has_team_stats into each form-list row),
  scripts/generate_metric_sql.py (one Surface), metric_map.csv (7 generated rows),
  tests/test_metric_map.py (one fan question), tests/test_export_site_data.py (two tests).
  site_v2/src/lib/types.ts declares has_team_stats; no component reads it.
  layer_rules: mart_team_momentum_window keeps its documented same-layer read, now of
  mart_team_window_metrics; no new model; check_layer_contract unchanged.
  deploy_order: the CI export runs teams and fixtures only; the matchstats entity has no CI
  caller. The prod table marts.mart_team_fixture_stats stays until the CPO drops it.
  blast_radius: mart_team_fixture_stats and the matchstats export disappear;
  mart_team_momentum_window keeps every row and column, and has_team_stats may change on rows
  where the provider's stat line and the match window disagree, counted before merge. No
  payload the site reads changes shape.

decisions_taken: >
  Approved in chat, 2026-10-14: the plan; has_team_stats reads mart_team_window_metrics' match
  window (games_with_team_stats > 0) for the played fixture and team; the fan question "How many
  corners did Dortmund win in their last match?" reads mart_team_window_metrics.corners_per_match
  with window_type match; these exact document texts: docs/content_architecture.md line 73
  becomes "| | Single fixture | team, player | `mart_team_window_metrics` (window_type match),
  `mart_player_fixture_stats` |"; docs/site_architecture.md, Fixture page row, the sentence "The
  played-match drill-down has no page; its export is `matchstats/{fixture_api_id}.json`, from
  `mart_team_fixture_stats` and `mart_player_fixture_stats`." is removed and nothing else
  changes; docs/wireframes/01_fixture_page.md, the data-source row for
  `data/matchstats/{played_fixture_sk}.json` is removed; dbt_project/docs/layering.md, the
  mart_team_fixture_stats row is removed.

  THRESHOLD DECLARATIONS: NEW MECHANISM: none; a removal. RECURRING COST: falls, one mart build
  less; measured before and after and put to the CPO in GiB.

decisions_reserved:
  - Dropping the prod tables no longer built: marts.mart_team_fixture_stats,
    marts.mart_player_match_log, marts.mart_team_momentum.
  - docs/wireframes/03_player_profile.md still links match-log rows to matchstats: the player
    page's design (#136).
  - GAP-07 in docs/wireframes/99_gaps_register.md and design-mocks/gen_match_page.py: the played
    match page (#175).

done_when:
  - generate_metric_sql.py --check and sync_metric_docs_blocks.py --check pass; the governance gates pass; dbt parse and compile pass; sqlfluff lint of mart_team_momentum_window is clean; the full pytest suite passes; npm run build in site_v2 exits 0 with no site_v2/src change.
  - data:build:mr is green, its tests included.
  - On prod data mart_team_momentum_window from the MR build equals prod on every key and on every column but has_team_stats; has_team_stats differences are counted and listed.
  - The warehouse read before and after is measured and put to the CPO.

amendments: >
  none.
