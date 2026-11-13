# Task contract — Statistics boards: catalogue, player and team leaderboards

objective: >
  Issues #139 and #140 (Statistics page and leaderboard; approved design on #139), with the ball
  actions boards of the #132 and #139 notes of 2026-11-10. Every player and team of a
  competition-season is ranked on every Statistics board, in mart_leaderboards and
  mart_team_leaderboards, with no top-10 cut. The rank ties on the shown value and skips the next
  place. Each row carries the shown value and the board's direction. The catalogue gains the four
  per-90 metrics and the approved metric_order. The competition dropdown's hand-set order is a
  seed. Match leaders and the season boards gain ball actions.

refs: >
  #139 approved design and notes of 2026-11-10; #140; #132 note of 2026-11-10 (ball actions in
  Match leaders); stream D plan and the coordinating session's rulings of 2026-11-12.

scope_paths:
  - dbt_project/seeds/metric_catalogue.csv
  - dbt_project/seeds/metric_map.csv
  - dbt_project/seeds/statistics_competitions.csv
  - dbt_project/seeds/schema.yml
  - dbt_project/dbt_project.yml
  - scripts/generate_metric_sql.py
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_player_season__metrics.sql
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season.yml
  - dbt_project/models/4_intermediate/shared/int_player_match__metrics.sql
  - dbt_project/models/4_intermediate/shared/int_player_match.yml
  - dbt_project/models/5_marts/shared/mart_leaderboards.sql
  - dbt_project/models/5_marts/shared/mart_team_leaderboards.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/models/docs/metric_columns.md
  - dbt_project/models/docs/metric_rules.md
  - dbt_project/macros/display_value.sql
  - dbt_project/tests/assert_mart_leaderboards_*.sql
  - dbt_project/tests/assert_mart_team_leaderboards_*.sql
  - tests/test_form_comparison_metric_set.py
  - tests/test_leaderboard_board_sets.py
  - tests/test_catalogue_order.py
  - tests/test_ranking_floors.py
  - tests/test_metric_rows.py
  - tests/test_export_site_data.py
  - tests/test_no_decision_history_in_code.py
  - site_v2/src/data/metric_rows.json
  - site_v2/src/data/player_metric_rows.json
  - .claude/task/139-statistics-boards/contract.md
  - .claude/task/139-statistics-boards/review.md
  - .claude/task/139-statistics-boards/review_input.patch
  - .claude/task/139-statistics-boards/acceptance_evidence.md

impact_map: >
  writers: dbt only; no ingestion change. Seeds: metric_catalogue gains four rows and new
  metric_order values; statistics_competitions is new. int_player_season__metrics gains four
  generated per-90 columns; int_player_match__metrics gains ball_actions_player.
  mart_leaderboards and mart_team_leaderboards keep their grain and gain boards, every ranked
  row (no top-10 cut), display_value and, on the player mart, rank_order.
  lineage: `dbt ls --resource-type model --select int_player_season__metrics+
  int_player_match__metrics+ mart_leaderboards+ mart_team_leaderboards+ metric_catalogue+`
  returns int_player_match__metrics, int_player_season__metrics, mart_leaderboards,
  mart_player_competition_benchmarks, mart_player_index, mart_player_profile,
  mart_team_competition_benchmarks, mart_team_leaderboards. mart_player_profile and
  mart_player_index name their columns from int_player_season__metrics, so the new columns stop
  there; the two benchmark marts read only the catalogue's direction.
  consumption: scripts/export_site_data.py, unchanged. The Rankings tab reads both marts with
  `league_leader_order <= 5`, Home with `league_leader_order = 1`, Match leaders with
  `window_type = 'match'`, each filtered to its own board tuple, so they read the same rows; the
  Rankings tab shows `rank`, which now skips after a tie. fetch_leaderboard_payloads reads every
  season row and keeps `rank <= 10` per board of its tuple, so its payload keeps its shape, with
  ranks that skip after a tie. fetch_metric_rows and fetch_player_metric_rows select by
  metric_order: their row ORDER follows the approved catalogue order and their row SET is
  unchanged (pinned by tests/test_form_comparison_metric_set.py); the committed
  site_v2/src/data/metric_rows.json and player_metric_rows.json are regenerated to match.
  layer_rules: check_layer_contract.py (no partition_by or cluster_by; marts read intermediates,
  core and seeds); generated metric SQL checked by tests/test_generate_metric_sql.py; the metric
  map and docs blocks by scripts/sync_metric_docs_blocks.py --check; descriptions by
  check_description_hygiene.py.
  deploy_order: additive except the season cut and the rank function; the deployed marts keep
  working until the merge, and the nightly rebuilds them after it.
  blast_radius: mart_leaderboards grows from 1.2M rows (438 MB) to about 4.5M rows; the team mart
  to at most about 0.6M rows. Rank values change where boards tie. The export's nightly read of
  mart_leaderboards grows with it (measured in the MR).

approved_design:
  - match: #132
  - player: #136

acceptance_criteria:
  - site_v2/src/data/metric_rows.json lists the same 34 metrics as on main, in the catalogue's new order: shots on target against moves after goals per shot on target, key passes before possession, and yellow and red cards before fouls and offsides.
  - site_v2/src/data/player_metric_rows.json lists the same 24 metrics as on main, in the catalogue's new order: key passes per 90 before ball actions per 90, and dribbles completed (per 90, percentage) before duels won (per 90, percentage).
  - No other file under site_v2/src changes.

decisions_taken: >
  The approved #139 design (approved in chat, 2026-11-10) gives the boards, forms, ranking
  direction and the catalogue order. The four per-90 descriptions: the CPO approved them as
  drafted (approved in chat, 2026-11-12). The percentage-board floor: the CPO decided 10
  attempts (approved in chat, 2026-11-12): shooting accuracy on shots, dribble success on
  dribbles attempted, duels won on duels, save percentage on shots on target faced; finishing
  keeps its 10 shots on target. The number rule, "10 or more whole, under 10 one decimal,
  percentages whole; order by the exact value; the rank follows the shown value", is the CPO's
  (approved in chat, 2026-11-11, #230 note 4208591574). Ties share a place with the next rank
  skipped, 1, 2, 2, 4 (approved in chat, 2026-11-10, on #230); it is sitewide, so it replaces
  #129's dense rank on every board, Rankings tab and Home included. The marts serve the shown
  value as display_value; rounding half away from zero on the decimal value is how BigQuery's
  ROUND works, an implementation detail. Penalty goals and share of team goals keep no
  metric_order in this MR: no current page reads them, and the Statistics page build takes their
  order from the #139 design. Goals against per 90 ranks goalkeepers only: the #139 design's
  "goals against (keepers)". shots_off_target_per_match,
  shots_blocked_per_match, cards_yellow_per_match and cards_red_per_match keep no metric_order, so
  the approved #132 Form comparison does not change: coordinator's ruling, 2026-11-12. The
  shots-on-target difference board ranks every team, zero and negatives included: the CPO decided
  it (approved in chat, 2026-11-12). The acceptance criteria for the two metric_rows files: the CPO
  approved them as drafted (approved in chat, 2026-11-12); the catalogue order reaches those two
  approved pages as a reordering only, their metric sets pinned by
  tests/test_form_comparison_metric_set.py.
  The ball actions boards' page wiring (the export's board tuples and the label in strings.ts)
  belongs to the page build. dribbles_past_per90 is ranked in mart_leaderboards, the one mart that
  serves the new per-90s, under the plain per-90 rule; no page shows it, and a goalkeeper with a
  zero rate can top this fewest-first board. Share of team goals ranks the player's row for the
  club the leaderboard row names.
  THE FOUR NEW CATALOGUE ROWS, as committed (description approved by the CPO as drafted, approved
  in chat, 2026-11-12; metric_order from the #139 design; label key, formula, format, group and
  direction follow the row's total twin; interpretation is the internal analyst reading, read by
  no page or export, in the house style of its twin):
  passes_accurate_per90: label playerMetrics.passesAccuratePer90.label; "The player's passes that
  reached a teammate, per 90 minutes played."; sum(passes_accurate) * 90 / sum(minutes);
  decimal_1; passing; higher_better; interpretation "Completed passes per 90; high = heavily
  involved in possession (a volume read; pass accuracy captures security)"; order 3/4.
  dribbles_attempts_per90: label playerMetrics.dribblesAttemptsPer90.label; "Times the player
  tried to dribble past an opponent, per 90 minutes played."; sum(dribbles) * 90 /
  sum(minutes); decimal_1; one_on_one; higher_better; interpretation "Take-ons attempted per
  90; high = willing to take players on (a volume read; the success rate shows how often it
  comes off)"; order 4/2.
  duels_per90: label playerMetrics.duelsPer90.label; "One-on-one challenges for the ball, on the
  ground or in the air, that the player contested, per 90 minutes played."; sum(duels) * 90 /
  sum(minutes); decimal_1; one_on_one; higher_better; interpretation "Duels contested per 90;
  high = a physically involved player (a volume read; the duel win rate captures efficiency)";
  order 4/7.
  dribbles_past_per90: label playerMetrics.dribblesPastPer90.label; "Times an opponent dribbled
  past the player, per 90 minutes played."; sum(dribbles_against) * 90 / sum(minutes);
  decimal_1; defending; lower_better; interpretation "Times beaten per 90; low = hard to get past
  (also tracks how often the player is the one defending)"; order 5/10.
  THE CHANGED metric_order VALUES are the #139 design's catalogue list, applied as recorded there:
  players Passing, One-on-one, Defending (dribbled past 9), Goalkeeping (shots on target faced
  6), Discipline and Playing time; teams Goals, Shooting (except off target 11 and blocked 12),
  Passing, Discipline (except yellow per match 2 and red per match 4), Goalkeeping and Set
  pieces. The four exceptions keep no metric_order, as above.
  THRESHOLD DECLARATIONS: one new seed (statistics_competitions, approved as "one table in the
  warehouse" in the #139 design). The export's nightly read of mart_leaderboards grows; measured
  and stated in the MR.

decisions_reserved:
  - none: every rule applied is named in decisions_taken with its approval

done_when:
  - python scripts/generate_metric_sql.py --check and scripts/sync_metric_docs_blocks.py --check pass
  - dbt parse passes; sqlfluff lint of every changed model and test passes
  - the changed marts, rebuilt as read-only queries against prod, pass every changed singular test
    and finish inside 300 s; row counts and bytes reported in the MR
  - full pytest passes

amendments: (none)
