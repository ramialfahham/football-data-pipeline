# Task contract — Team page redesign: retire the same-N comparison

objective: >
  Issue #250. The club Team page compares this season so far against the whole of last season
  (mart_team_page_window_metrics, merged on main c1084493). The earlier comparison, each season
  through the team's first N matches, is no longer read by any page: int_team_profile__yoy and its
  columns on mart_team_profile, and metric_value_prev_season on the team benchmarks. The player's
  same kind of comparison, int_player_profile__yoy (each season through the player's first N
  appearances at the club, plus last season's full totals) and its columns on mart_player_profile,
  is read by no page either: the Player page compares through mart_player_window_metrics. This
  removes both with their tests and descriptions, and rule R6 states the team's window.

refs: >
  #250, the design approved in chat, 2026-11-06, and its explainers in note 4254003834. The reader
  inventory and the removal, the national Standing reads included, and the player chain's place in
  this MR were ruled by the coordinating session on 2026-11-18. The R6 text, the two
  content_architecture lines that name the window marts, and the removal of the catalogue metric
  points_rank (added on #235): approved in chat, 2026-11-18, through the coordinating session.

scope_paths:
  - dbt_project/models/4_intermediate/shared/int_team_profile__yoy.sql
  - dbt_project/models/4_intermediate/shared/int_team_profile.yml
  - dbt_project/models/4_intermediate/shared/int_team_competition_benchmark_metrics_long.sql
  - dbt_project/models/4_intermediate/shared/int_competition_benchmarks.yml
  - dbt_project/models/4_intermediate/shared/int_player_profile__yoy.sql
  - dbt_project/models/4_intermediate/shared/int_player_profile.yml
  - dbt_project/models/4_intermediate/shared/int_player_profile__contribution.sql
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season__metrics_cumulative.sql
  - dbt_project/models/5_marts/shared/mart_team_profile.sql
  - dbt_project/models/5_marts/shared/mart_team_competition_benchmarks.sql
  - dbt_project/models/5_marts/shared/mart_player_profile.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/models/docs/shared_columns.md
  - dbt_project/models/docs/metric_columns.md
  - dbt_project/models/docs/metric_rules.md
  - dbt_project/seeds/metric_map.csv
  - dbt_project/seeds/metric_catalogue.csv
  - dbt_project/tests/assert_team_yoy_pairs_the_same_games_played.sql
  - dbt_project/tests/assert_team_benchmark_prev_season_matches_yoy.sql
  - scripts/export_site_data.py
  - scripts/declare_missing_columns.py
  - scripts/sync_metric_docs_blocks.py
  - tests/test_sync_metric_docs_blocks.py
  - tests/test_metric_map.py
  - tests/test_sentence_length_in_docs.py
  - tests/test_export_site_data.py
  - tests/test_no_decision_history_in_code.py
  - design-mocks/gen_team_mock.py
  - docs/content_architecture.md
  - docs/ui_design_brief.md
  - docs/metrics_context_model.md
  - dbt_project/models/4_intermediate/shared/int_season_record.yml
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season.yml
  - dbt_project/models/4_intermediate/shared/int_player_season_record.sql
  - dbt_project/models/4_intermediate/shared/int_team_season_record.sql
  - dbt_project/tests/assert_season_rates_inputs_covered.sql
  - dbt_project/seeds/schema.yml
  - dbt_project/docs/layering.md
  - .claude/task/250-same-n-retire/contract.md
  - .claude/task/250-same-n-retire/review.md
  - .claude/task/250-same-n-retire/review_input.patch

impact_map: >
  writers: dbt only; no ingestion change. Removed: int_team_profile__yoy (model, its yml entry and
  four tests), assert_team_yoy_pairs_the_same_games_played, assert_team_benchmark_prev_season_matches_yoy.
  Changed: mart_team_profile loses its 59 year-over-year columns (yoy_games_played_cutoff,
  points_this_season, points_prev_season, points_delta_yoy, points_rank_prev_season, goals for and
  against, and the 16 rates, each this season, previous season and delta);
  int_team_competition_benchmark_metrics_long, int_team_competition_benchmarks' docs and
  mart_team_competition_benchmarks lose metric_value_prev_season and the cumulative read behind it.
  int_team_season__metrics_cumulative and int_team_season__table_by_time stay: other models read them.
  Player: int_player_profile__yoy (model, its yml entry and its tests) is removed, and
  mart_player_profile loses its 22 year-over-year columns (yoy_appearances_cutoff, the five
  metrics' this season, previous season and delta, appearances_prev_full and the five
  _prev_season_full totals). int_player_season_record and int_player_profile__contribution stay.
  `dbt ls --resource-type model --select int_player_profile__yoy+` returns int_player_profile__yoy
  mart_player_index mart_player_profile; mart_player_index reads identity columns only.
  Seed: metric_catalogue loses the row points_rank; the export's metrics.json (the whole catalogue,
  read by no page) loses it with it.
  lineage: `dbt ls --resource-type model --select int_team_profile__yoy+` returns
  int_team_profile__yoy mart_player_index mart_team_index mart_team_profile; mart_team_index and
  mart_player_index read only team_sk from mart_team_profile. `dbt ls --resource-type model --select
  int_team_competition_benchmark_metrics_long+` returns int_team_competition_benchmark_metrics_long
  int_team_competition_benchmarks mart_team_competition_benchmarks.
  consumption: export_site_data.py reads mart_team_profile with select * into the team payload's
  seasons[], and ships benchmarks[].metric_value_prev_season; both leave the payload. In site_v2,
  TeamStanding.astro (national team pages only) reads points_this_season, points_prev_season and
  points_rank_prev_season, and [team].astro's hasPerformance reads points_this_season. Measured on
  prod, all three are NULL on all 215 national featured-season rows (the model is domestic leagues
  only), and on 0 club rows does points_this_season decide hasPerformance; format.ts gives the dash
  for null and undefined alike, so no page changes. design-mocks/gen_team_mock.py reads the cutoff
  and the this-season and previous-season columns for its last-season table. The export reads
  mart_player_profile by a fixed column list that holds none of the player columns, and no site_v2
  file names them; the Player page's comparison reads mart_player_window_metrics.
  ci_layer_rules: scripts/check_layer_contract.py, scripts/check_description_hygiene.py,
  scripts/check_relationships_coverage.py, scripts/sync_metric_docs_blocks.py --check,
  tests/test_metric_map.py. sync_metric_docs_blocks.py refuses to run when it matches fewer
  derived column names than its floor, MIN_DERIVED 40; the removal leaves fewer, so the floor
  moves to just under the real count it leaves.
  deploy_order: one merge; the nightly rebuilds mart_team_profile and the benchmark models without
  the columns. The retired table int_team_profile__yoy stays in BigQuery until dropped; nothing reads it.
  blast_radius: no displayed number changes, proved by an export payload diff on a sample of team
  pages with a national team and a sample of player pages. The team payload loses the
  year-over-year keys from seasons[] and metric_value_prev_season from benchmarks[]; the player
  payload does not change. A BI reader of mart_team_profile or mart_player_profile loses the
  first-N columns.

approved_design:
  - team: #134

depends_on:
  - none: the window mart this replaces the old comparison with is merged (main c1084493)

shared_files:
  - none: no design baseline, registry or screenshot fixture changes

decisions_taken: >
  The national Standing block keeps its reads of points_this_season, points_prev_season and
  points_rank_prev_season while the payload no longer carries them; the values were NULL for every
  national team, the page renders the same dash, and the national team page's own redesign removes
  the reads (ruled by the coordinating session, 2026-11-18). site_v2 is not touched.
  gen_team_mock.py's last-season table reads the payload's last_season (the whole-season window) and
  the explainer approved in #250 note 4254003834, in place of the first-N columns. The generator's
  full run already fails on main before that table, on the built page's season selector, and stays
  counted as a failing generator in the design inventory baseline; rewriting it for the new page is
  not this task. Rule R6 gains the words that give teams the all-competitions window; the other three
  docs only lose the first-N words, and content_architecture names the window marts in place of the
  retired models, each by the exact lines approved (refs). The catalogue metric points_rank leaves
  the catalogue: its only column was points_rank_prev_season, and nothing else reads it; its
  generated doc block and map row regenerate. The fan-question test in tests/test_metric_map.py keeps its twenty
  questions: the two that named the retired player columns are answered by the columns that hold
  the same facts now, mart_player_career (a season's goals at a club) and
  mart_player_window_metrics (this season against last). No new mechanism. No recurring cost added; the nightly reads less (dry-run sizes in the MR).

decisions_reserved:
  - none: the removal of points_rank and the exact text of R6 and the three docs are approved (refs);
    no page output changes

done_when:
  - dbt parse succeeds from the repo root.
  - python scripts/sync_metric_docs_blocks.py --check, check_layer_contract.py,
    check_description_hygiene.py and check_relationships_coverage.py pass.
  - python -m pytest tests -q is green.
  - SQLFluff adds no violation on any changed model.
  - git grep finds no yoy_games_played_cutoff, yoy_appearances_cutoff, int_team_profile__yoy,
    int_player_profile__yoy or team metric_value_prev_season outside the window marts.
  - Dry-run bytes of mart_team_profile and the benchmark models, before and after, are in the MR.
  - The team payloads of a sample with a club and a national team differ from main's only by the
    removed keys, and the player payloads of a sample do not differ.
  - ci_local --mr is green; CI's data:build:mr is green; merge_ready says ready.

amendments:
  - 2026-11-18: + dbt_project/models/4_intermediate/shared/int_season_record.yml,
    dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season.yml,
    dbt_project/models/4_intermediate/shared/int_player_season_record.sql,
    dbt_project/models/4_intermediate/shared/int_team_season_record.sql,
    dbt_project/tests/assert_season_rates_inputs_covered.sql, dbt_project/seeds/schema.yml —
    authority: engineering_standards.md section 2, a description states what the table holds
    (analytics-engineer-reviewer, round 1); content: the descriptions and comments lose the words
    that name the removed year-over-year content, and the metric_map variant description loses
    the four variants no map row carries.
  - 2026-11-18: + dbt_project/docs/layering.md — authority: the CPO, approved in chat, 2026-11-18,
    through the coordinating session (analytics-engineer-reviewer, round 1); content: the
    mart_team_profile row loses "YoY deltas", strip-only.
  - 2026-11-18: + tests/test_sentence_length_in_docs.py — authority: the standing rule that a pin
    moves only down, and is lowered in the change that lowers it (ci_local test:python); content:
    the metric_columns.md pin from 15 to 4, after the removed same-N blocks took 11 long
    sentences with them.
