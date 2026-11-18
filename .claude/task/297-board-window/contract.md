# Task contract — the export's eighth Match leaders board and the season record's window

objective: >
  Two defects found while building #297. (A) The export lists seven Match leaders boards while
  mart_leaderboards serves eight in prod: shape_match_leaders refuses the eighth,
  ball_actions_player, so every export that writes played matches fails, deploy:export on main
  included. The export gains the board and its name; the test that let it through checks equality.
  (B) mart_player_season_record falls back to the previous season when the team has no player rows
  in the fixture's competition this season, even after the team has played there. The previous
  season is the window only before the team's first match in the competition.

refs: >
  #297; #132 note of 2026-11-10 17:43 (Match leaders gains a Ball actions board, approved in chat);
  #132 note of 2026-11-10 19:14 (the Players to watch window, approved in chat); the coordinating
  session's ruling of 18 Nov 2026 that both ship before the Players to watch block.

depends_on:
  - none: both fixes stand on gitlab/main a54adfbf

shared_files:
  - scripts/export_site_data.py
  - site_v2/src/i18n/strings.ts

scope_paths:
  - .claude/task/297-board-window/
  - dbt_project/models/5_marts/shared/mart_player_season_record.sql
  - dbt_project/tests/assert_player_season_record_window_follows_team_matches.sql
  - scripts/export_site_data.py
  - tests/test_leaderboard_board_sets.py
  - site_v2/src/i18n/strings.ts

impact_map: >
  writers: dbt only for B (mart_player_season_record); scripts/export_site_data.py for A. No
  ingestion change.
  lineage: `dbt ls --select mart_player_season_record+ --resource-type model` returns only
  football_data_pipeline.5_marts.shared.mart_player_season_record. Its only reader is
  scripts/export_site_data.py (the fixture payload's Players to watch).
  B measured: the compiled new mart run read-only against prod (18 Nov 2026, 90 MB) drops exactly
  89 of 6,641 upcoming sides, all whose team has played the fixture's competition this season
  without player rows there; no other side changes window; 0 sides show the previous season after
  their team has played. Rows go from 164,802 to 162,737; no grain or column change.
  A measured: prod mart_leaderboards serves eight match boards (test_leaderboard_board_sets.py
  reads the mart's match_boards list: eight); the export listed seven; the full export of 18 Nov
  2026 stopped in shape_match_leaders with KeyError ball_actions_player. The played match page's
  Match leaders shows the Ball actions board; its name key playerMetrics.ballActions.label had no
  entry in METRIC_TERMS. The 11 committed played samples are not re-exported, so the committed site
  sample does not change.
  layer_rules: check_layer_contract.py (marts read intermediates and core); the export selects
  and does not rank (A5).
  deploy_order: data:build:mr builds the mart in the MR's own datasets; prod takes it at the
  data:build:main after the merge. The export change is read at the next export run.
  blast_radius: Players to watch rows of 89 upcoming sides leave the mart (they showed last
  season); played match pages gain the Ball actions board. No other number changes.

approved_design:
  - match: #132

decisions_taken: >
  The Ball actions board takes the catalogue's place (passing group, after key passes) and the
  catalogue label, as #132's note of 2026-11-10 17:43 says. The window rule is #132's note of
  2026-11-10 19:14. A team that has played the competition this season without player rows has no
  rows in the mart; awarded results are no match played, as team_matches already counts them.
  Shipping both before the Players to watch block is the coordinating session's ruling of 18 Nov
  2026.

decisions_reserved:
  - none: both rules applied are in #132's notes of 2026-11-10

acceptance_criteria:
  - The played match page's Match leaders shows a Ball actions board whose name resolves in EN, DE and FI.

done_when:
  - dbt parse passes; sqlfluff lint of the mart and the new test passes
  - python -m pytest tests/test_leaderboard_board_sets.py tests/test_export_site_data.py passes
  - npm test in site_v2 passes and python scripts/check_copy_gate.py passes
  - python scripts/ci_local.py --mr is green
  - the MR pipeline, data:build:mr included, is green and python scripts/merge_ready.py <iid> says ready

amendments: (none)
