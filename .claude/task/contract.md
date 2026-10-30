# Task contract — appearances as a catalogue metric

objective: >
  The Team page's Squad tab (#235) shows appearances, minutes per appearance, goals and assists,
  and on-screen metric names come only from the catalogue. Appearances becomes a catalogue metric
  with its formula, generated into the models that compute it today, with the same value: matches
  with minutes > 0, 0 for a squad member never brought on, blank where a match's minutes are
  unknown or the club has a played match with no player data.

refs: >
  #235 (What exactly: appearances and minutes per appearance as catalogue metrics); plan approved
  in chat, 2026-10-30.

scope_paths:
  - dbt_project/seeds/metric_catalogue.csv
  - dbt_project/seeds/metric_map.csv
  - dbt_project/seeds/player_season_answer_key.csv
  - dbt_project/models/docs/metric_rules.md
  - dbt_project/models/docs/*.md
  - dbt_project/models/4_intermediate/shared/int_player_club_season__metrics.sql
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_player_season__metrics.sql
  - dbt_project/models/4_intermediate/shared/int_player_season_position__metrics.sql
  - dbt_project/models/5_marts/shared/mart_player_career.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/tests/assert_no_uncatalogued_season_metric.sql
  - scripts/generate_metric_sql.py
  - docs/wireframes/11_team_squad.md
  - docs/wireframes/03_player_profile.md
  - docs/wireframes/13_player_career.md
  - dbt_project/seeds/schema.yml
  - tests/test_*.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md

impact_map: >
  writers: int_player_club_season__metrics, int_player_season__metrics and
  int_player_season_position__metrics, whose hand-written appearances column becomes the generated
  one with the same guard. downstream, pasted from `dbt ls --resource-type model --select
  int_player_club_season__metrics+ int_player_season__metrics+
  int_player_season_position__metrics+` (9 models, the three writers included):
  int_player_season__metrics, int_player_club_season__metrics,
  int_player_competition_benchmark_metrics_long, int_player_competition_benchmarks,
  int_player_season_position__metrics, mart_leaderboards, mart_player_career,
  mart_player_competition_benchmarks, mart_player_profile. layer_rules: the formula in the
  catalogue, computed in the intermediates. deploy_order: the MR data build. blast_radius: none in
  values; the column's description and the metric map change, and the drift test no longer
  exempts appearances.

approved_design:
  - none: no page output changes

decisions_taken: >
  The plan, approved in chat, 2026-10-30, with its exact texts: rule R7 loses "appearances, "; the
  catalogue row appearances (player, countif(minutes > 0) on int_legs__player_match, integer,
  playing_time, neutral) with its description and interpretation; the Squad wireframe's sentence
  on catalogue metrics. The label text comes with the page. No new mechanism, no dependency, no
  recurring cost.

decisions_reserved:
  - The EN, DE and FI label text for appearances, with the page.

done_when:
  - generate_metric_sql.py --check and sync_metric_docs_blocks.py --check pass.
  - dbt parse, SQLFluff on the changed models, the offline gates and pytest pass.
  - The MR data build passes every catalogue and value test as an error, the answer key included.

amendments: >
  Round 1 of the review: docs/wireframes/03_player_profile.md enters scope, its section 4 saying
  appearances is a catalogue metric and starts, substitute appearances and minutes are facts, text
  approved in chat, 2026-10-30; int_player_season_position__metrics enters scope, the third model
  that computes appearances today, which the objective covers; the impact map carries the dbt ls
  output. Round 2: docs/wireframes/13_player_career.md enters scope, its two lines naming
  appearances a catalogue metric with its label and format from the catalogue, text approved in
  chat, 2026-10-30; dbt_project/seeds/schema.yml enters scope, its metric_group description naming
  appearances under playing_time, text approved in chat, 2026-10-30. Round 3: the second sentence
  of 03_player_profile.md section 4 is in the active voice, text approved in chat, 2026-10-30.
