# Task contract — Ball actions, a new player metric

objective: >
  The catalogue gains two player metrics: ball_actions_player, the passes, shots, dribbles,
  tackles, interceptions, blocks and saves a player made, and ball_actions_per90, the same per 90
  minutes played. The generator writes both into the player season models; the count is served in
  mart_player_profile and the per 90 in the position-peer comparison, as every existing count and
  per-90 metric is. A hand-worked answer key proves both values.

refs: >
  #136, the Player page review, where the metric was defined (definition, texts, group and
  direction approved in chat, 2026-11-01, recorded on #136; this MR's plan approved in chat,
  2026-11-01).

scope_paths:
  - dbt_project/seeds/metric_catalogue.csv
  - dbt_project/seeds/metric_map.csv
  - dbt_project/seeds/player_season_answer_key.csv
  - dbt_project/seeds/schema.yml
  - scripts/generate_metric_sql.py
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_player_season__metrics.sql
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season.yml
  - dbt_project/models/4_intermediate/shared/int_player_club_season__metrics.sql
  - dbt_project/models/4_intermediate/shared/int_player_season_position__metrics.sql
  - dbt_project/models/4_intermediate/shared/int_player_season_position.yml
  - dbt_project/models/4_intermediate/shared/int_player_competition_benchmark_metrics_long.sql
  - dbt_project/models/4_intermediate/shared/int_competition_benchmarks.yml
  - dbt_project/models/5_marts/shared/mart_player_profile.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/models/docs/metric_columns.md
  - docs/wireframes/12_player_stats.md
  - docs/wireframes/metrics_display.md
  - tests/test_no_decision_history_in_docs.py
  - tests/test_sentence_length_in_docs.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md

impact_map: >
  `.venv/Scripts/dbt.exe ls --project-dir dbt_project --select int_player_season__metrics+
  int_player_season_position__metrics+ int_player_competition_benchmark_metrics_long+
  mart_player_profile+ metric_catalogue+ player_season_answer_key+ --resource-type model` lists
  int_player_competition_benchmark_metrics_long, int_player_competition_benchmarks,
  int_player_season__metrics, int_player_season_position__metrics, mart_leaderboards,
  mart_player_competition_benchmarks, mart_player_profile, mart_team_competition_benchmarks,
  mart_team_leaderboards.
  The two season models and mart_player_profile gain columns; the benchmark models gain
  ball_actions_per90 rows for every player-season-position that clears the existing floors. The
  team marts and mart_leaderboards read the catalogue but select team rows or named boards, so
  they gain nothing. On prod data the season model keeps its 193,804 rows. The glossary export
  (metrics.json, not deployed) gains the two catalogue rows, and the player payload (`players`,
  not in the deploy's export list) gains `seasons[].ball_actions_player` and a
  `ball_actions_per90` benchmark member. No page reads any of it.
  blast_radius: two new columns and new benchmark rows; no existing value changes.

approved_design:
  - none: no page output changes; no page shows either metric, and the labels ship with the page that first does

decisions_taken: >
  Approved in chat, 2026-11-01: the definition (passes + shots + dribbles + tackles +
  interceptions + blocks + saves, duels left out), the count and per-90 forms, the ids, the
  description and interpretation texts, group Passing and direction higher_better; labels ship
  with the page that first shows the metric. The plan approved in chat, 2026-11-01: the count is
  served in mart_player_profile and the per 90 in the position-peer comparison for all four
  positions, like passes_per90.

decisions_reserved:
  - "none: every decision of this task is approved, see decisions_taken"

acceptance_criteria:
  - "The catalogue holds ball_actions_player and ball_actions_per90 with the approved formula, texts, group Passing and direction higher_better."
  - "int_player_season__metrics carries both, written by the generator; mart_player_profile serves the count and mart_player_competition_benchmarks serves the per 90 for all four positions."
  - "The answer key proves both values for the five hand-worked player-seasons."
  - "No existing column or row count changes."

amendments:
  - "Implementation within the approved plan, reported in chat, 2026-11-01: the generator gains one more layout, a null check split at its first 'and', used only when no other layout fits; it changes no existing metric's SQL."
  - "Approved in chat, 2026-11-01, strip-only: 12_player_stats.md and metrics_display.md stop restating the benchmark set's count, members and directions and point to the catalogue's direction column and to int_player_competition_benchmark_metrics_long; the benchmark model and yml descriptions drop the set's count. The two doc ratchet tests lower their pinned counts for the two files, as the tests require when a cleanup removes history lines or long sentences."

  - "Approved in chat, 2026-11-01: the two rows' descriptions name the passes, shots and dribbles the player attempted and the tackles, interceptions, blocks and saves the player made; the interpretation reads as involvement in play on or off the ball, and the count adds the raw-count minutes caveat."
  - "Approved in chat, 2026-11-01: the per-90 description drops its second 'the player' to stay within the docs sentence limit."

done_when:
  - The generator and docs-sync checks, dbt parse, SQLFluff, pytest, the offline gates and the site's node tests pass.
  - The changed models run on prod data give the answer key's values and change no existing column or row count.
