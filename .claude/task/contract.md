# Task contract — a window of one played match on mart_leaderboards

objective: >
  mart_leaderboards serves each played match as a window of one: for every played match with
  player stats, seven count boards (Shots, Passes, Key passes, Dribbles attempted, Duels won,
  Defensive actions, Fouls), each the top three across both teams, a shared count sharing the
  rank, a tie at the cut won by fewer minutes, so the played match page's Match leaders block can
  read them. A new player metric fouls_player joins the catalogue, and three metrics get their
  place in the catalogue's order. The season boards, every existing payload and every page stay
  the same.

refs: >
  #176 (https://gitlab.com/rami.al-fahham/football-data-pipeline/-/work_items/176), the line
  "mart_leaderboards serves a window of one match: each player's counts in that match". The
  Match leaders block is #175, its design approved on #132. The plan, the fouls_player metric,
  its texts and the catalogue order in decisions_taken: approved in chat, 2026-10-14.

scope_paths:
  - dbt_project/seeds/metric_catalogue.csv
  - dbt_project/seeds/metric_map.csv
  - dbt_project/models/docs/metric_columns.md
  - site_v2/src/i18n/strings.ts
  - scripts/generate_metric_sql.py
  - dbt_project/models/4_intermediate/shared/int_player_match__metrics.sql
  - dbt_project/models/4_intermediate/shared/int_player_match.yml
  - dbt_project/models/5_marts/shared/mart_leaderboards.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/tests/assert_mart_leaderboards_board_leader_order_is_total.sql
  - dbt_project/tests/assert_mart_leaderboards_every_home_board_has_a_leader.sql
  - dbt_project/tests/assert_mart_leaderboards_one_leader_per_league.sql
  - dbt_project/tests/assert_one_current_season_per_league.sql
  - dbt_project/tests/assert_player_metrics_follow_catalogue_formula.sql
  - dbt_project/tests/assert_mart_leaderboards_match_boards_follow_the_rule.sql
  - dbt_project/docs/layering.md
  - scripts/export_site_data.py
  - tests/test_catalogue_order.py
  - tests/test_export_landing.py
  - tests/test_export_site_data.py
  - tests/test_leaderboard_board_sets.py
  - tests/test_metric_map.py
  - tests/test_generate_metric_sql.py
  - tests/test_no_decision_history_in_code.py
  - tests/test_no_decision_history_in_docs.py
  - tests/test_sentence_length_in_docs.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md

impact_map: >
  writers: dbt builds the new int_player_match__metrics from int_legs__player_match, and
  mart_leaderboards from int_player_season__metrics, the new intermediate, dim_player and
  dim_team. The catalogue seed and the metric map seed are configuration. No ingestion writer.
  downstream: pasted output of `dbt ls --select int_player_match__metrics+ mart_leaderboards+
  metric_catalogue+ --resource-type model --output name` on the branch (dbt 1.7.20), 3 models:
  int_player_match__metrics mart_leaderboards mart_team_leaderboards.
  The same selection with --resource-type test, singular tests only (names starting assert_),
  20 tests: assert_form_window_rates_inputs_covered
  assert_mart_leaderboards_board_leader_order_is_total
  assert_mart_leaderboards_every_home_board_has_a_leader
  assert_mart_leaderboards_match_boards_follow_the_rule
  assert_mart_leaderboards_one_leader_per_league assert_mart_team_leaderboards_all_boards_present
  assert_mart_team_leaderboards_every_board_has_a_leader
  assert_mart_team_leaderboards_one_leader_per_league
  assert_mart_team_leaderboards_rank_follows_rank_order assert_metric_catalogue_expr_resolvable
  assert_metric_catalogue_unique_by_entity assert_metric_group_order_is_one_per_group
  assert_metric_meaning_complete assert_no_uncatalogued_season_metric
  assert_one_current_season_per_league assert_player_metrics_follow_catalogue_formula
  assert_player_season_answer_key assert_season_rates_inputs_covered
  assert_team_metrics_follow_catalogue_formula assert_team_season_answer_key.
  mart_team_leaderboards and the team tests read the catalogue seed; this change edits only
  player rows of it, so their reach is the seed reload alone. The catalogue seed is also read by
  scripts/generate_metric_sql.py, scripts/sync_metric_docs_blocks.py and the export's board
  order (_in_catalogue_order).
  Outside dbt: scripts/export_site_data.py (fetch_competition_payloads,
  fetch_leaderboard_payloads, fetch_landing_payload), the Python tests named in scope,
  site_v2/src/i18n/strings.ts (one new label key).
  layer_rules: the match window's selection and its catalogue formulas live in the new
  intermediate (metrics_context_model.md section 8.1); the mart ranks and cuts. Generic, not per
  competition; check_layer_contract unchanged.
  deploy_order: the seeds load before the models in data:build:mr, data:build:main and
  fdp-nightly. The export reads window_type, which the mart has only after the first build on
  main; the CI export runs teams and fixtures only.
  blast_radius: mart_leaderboards gains match rows, at most 21 per played match with player
  stats (seven boards, match_leader_order cut at three; the new singular test holds it) and
  three columns (window_type, fixture_sk,
  match_leader_order); every season row keeps its values and key. The catalogue gains
  fouls_player; shots_on_goal_player, finishing_efficiency_player_pct, cards_yellow_player and
  cards_red_player move one place down with their relative order kept, so no page changes.

acceptance_criteria:
  - Every committed sample payload under site_v2/src/data is byte-identical to main's; git diff gitlab/main -- site_v2/src/data lists nothing.
  - The built site's every page is byte-identical on the branch and on main, compared by script over the built output.
  - The export reads only season rows of mart_leaderboards (window_type season_to_date) in all three of its leaderboard reads; unit tests show each filter.

decisions_taken: >
  Approved in chat, 2026-10-14: the plan; a new catalogue metric fouls_player, sum(fouls) over
  int_legs__player_match, description "Fouls the player committed.", interpretation "Fouls
  committed - free kicks given away in the window; low = disciplined (high can also mean a player
  who breaks up play).", format integer, group discipline, direction lower_better, tier 3, label
  key playerMetrics.fouls.label with the words the team metric shows (EN "Fouls", DE "Fouls",
  FI "Rikkeet"); the catalogue order shots_player 1, shots_on_goal_player 2,
  finishing_efficiency_player_pct 3 in shooting, duels_won_player 3 in one_on_one, fouls_player
  1, cards_yellow_player 2, cards_red_player 3 in discipline; the match boards and their rule as
  #175 states them (top three, a shared count sharing the rank, a tie at the cut won by fewer
  minutes, no zero); and this dbt_project/docs/layering.md row text: "| `mart_leaderboards` |
  (player_sk, season_sk, metric_key) on season rows; (fixture_sk, player_sk, metric_key) on match
  rows | LONG per-board player leaderboards: the thirteen season boards of the competition page's
  Rankings tab (11 count + 2 rate, the rate boards behind a minutes and position floor), top 10
  per board; and seven count boards for each played match (window_type match), top three.
  Composes `int_player_season__metrics` and `int_player_match__metrics`; DENSE_RANK ties share,
  every board most first, a zero never ranked. |"

  THRESHOLD DECLARATIONS: NEW MECHANISM: none; one intermediate on the existing generated-surface
  pattern and one more window on an existing mart. RECURRING COST: rises with the new
  intermediate and the match rows in every build; measured before and after and put to the CPO
  in GiB.

decisions_reserved:
  - Renaming mart_leaderboards (#102).
  - Removing mart_team_fixture_stats and the old match-stats export: the next line of #176.
  - What the played match page shows for a board with fewer than three players, or none: #175.

done_when:
  - generate_metric_sql.py --check and sync_metric_docs_blocks.py --check pass; the copy gate passes; dbt parse and compile pass; sqlfluff lint of the changed models is clean; the full pytest suite passes.
  - data:build:mr is green, its tests included.
  - On prod data the season rows of the MR's mart equal prod mart_leaderboards in every key and column; the match boards hold at most three rows each, none zero.
  - The acceptance criteria are shown in acceptance_evidence.md.
  - The warehouse read before and after is measured and put to the CPO.

amendments: >
  The layering.md row text in decisions_taken is one sentence of 32 words, which the sentence-length
  gate refuses. It is replaced by the same facts in short sentences, approved in chat, 2026-10-14:
  "| `mart_leaderboards` | (player_sk, season_sk, metric_key) on season rows; (fixture_sk,
  player_sk, metric_key) on match rows | LONG per-board player leaderboards. The season rows are
  the thirteen boards of the competition page's Rankings tab, top 10 per board: 11 count and 2
  rate. The rate boards sit behind a minutes and position floor. The match rows are seven count
  boards for each played match (window_type match), top three. Composes
  `int_player_season__metrics` and `int_player_match__metrics`; DENSE_RANK ties share, every
  board most first, a zero never ranked. |"
  layering.md lists marts only, so the new intermediate gets no row there.
  After the MR build: site_v2/scripts/check-metric-labels.test.mjs refuses a metric label that no
  page asks for, and no page shows fouls_player yet. So playerMetrics.fouls.label leaves
  strings.ts in this change; its approved words (EN "Fouls", DE "Fouls", FI "Rikkeet") go in
  with the played match page (#175), the first page that shows it, as the labels of shots_player
  and duels_won_player will. The catalogue row keeps its label key. The third acceptance
  criterion and the first two are unchanged; site_v2/src is now untouched by this change.
