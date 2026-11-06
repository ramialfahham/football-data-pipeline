# Task contract — the Player page's data: window flag and export

objective: >
  Issue #259, step 2. mart_player_fixture_stats marks the matches of the season a Player page shows,
  and the export writes the payload the approved design (#136) reads: header, tabs, cards, next
  matches, the comparisons, last season and recent matches, for the players the site links to. No
  page reads it yet, so no page output changes.

refs: >
  #259, plan approved in chat 2026-11-06. Design: #136. Models: !382 (#256), !383 (#257).

scope_paths:
  - dbt_project/models/5_marts/shared/mart_player_fixture_stats.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - scripts/export_site_data.py
  - tests/test_export_site_data.py
  - tests/test_no_decision_history_in_code.py
  - dbt_project/tests/assert_player_page_windows.sql
  - dbt_project/docs/layering.md
  - docs/site_architecture.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md

impact_map: >
  writers: dbt only. mart_player_fixture_stats gains two columns, is_in_page_window and
  match_involvement, and season_sk inside its fixtures step. No ingestion change.
  lineage: `dbt ls --resource-type model --select mart_player_fixture_stats+` returns
  5_marts.shared.mart_player_fixture_stats, 5_marts.shared.mart_team_momentum_window. The second
  reads fixture_sk and team_sk only (mart_team_momentum_window.sql line 52), so the new column
  reaches nothing. `dbt ls --resource-type model --select +int_player_page__window_seasons` holds no
  mart, so the new ref makes no cycle.
  consumption: scripts/export_site_data.py is the mart's other reader. `--entities players` is not in
  deploy:export, and the Player page reads boards, not players/*.json, until the next MR.
  player_metric_rows.json is written by the metric_rows entity and committed with the page.
  ci_layer_rules: scripts/check_layer_contract.py, scripts/check_description_hygiene.py.
  deploy_order: one merge; the nightly dbt build adds the column. The sample export that needs it
  runs after that, for the next MR.
  blast_radius: no number changes; the mart gains a boolean. The grain holds because a player's
  window seasons are unique per window type, and a club season and a national one never coincide.
  The old player payload (seasons, match_log, career) has no reader: `grep -rn "match_log"
  site_v2/src --include=*.astro` returns nothing.

approved_design:
  - player: #136

decisions_taken: >
  From the plan on #259. Recent matches cover the season shown, so the mart gets a flag (decision 2).
  The set of players with a page does not change, so the export writes the players the Home and
  competition boards link to, read from the landing and competition payloads of the same run
  (decision 1). Peer values go in one shared file per competition, season and position, because a
  player's file would otherwise repeat them for every peer. Player metric rows are written beside
  metric_rows.json as player_metric_rows.json, leaving that file and its readers untouched. The plan
  said "in metric_rows.json"; a separate file changes no shipped build input in this MR. No new
  mechanism, no new dependency, no recurring cost: players joins the export in the next MR.
  The mart also serves match_involvement, played or on_bench, so the export only filters. A squad
  member with 0 minutes listing the matches "On the bench" is the design on #136. The Player row of
  docs/site_architecture.md changes with the exact text the CPO approves. Wireframe 03's data
  section stays until the next MR retires the file: #136 states its design wins over wireframes 03,
  12 and 13, and the plan on #259 takes every wireframe line to the CPO before that MR.

decisions_reserved:
  - Whether the cards use line-ups and goal records for a match with no player stats (#256, open). The payload carries the blank.
  - What the Club tab shows for a player with no club football (#256, open). The payload carries only the tabs the data marks.
  - Which further players get a page (#259, not in scope).

done_when:
  - python -m pytest tests passes.
  - dbt parse and sqlfluff pass on mart_player_fixture_stats.
  - data:build:mr is green, assert_player_page_windows included, which holds each tab's played matches equal to its Appearances card.

amendments: (none)
