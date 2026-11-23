# Task contract — hand-worked values for every metric new to the Player page

objective: >
  Every metric new to the Player page has a hand-worked value test on the window key and on the
  Squad key as well as on the season key. The window key gains ball_actions_per90, offsides_per90
  and goals_against_per90 (the goalkeeper case). The Squad key gains the median and ranks, ties
  included, of ball_actions_per90, shots_per90, shots_on_goal_player_pct, fouls_per90 and
  offsides_per90 for one past squad whose every input is present. Each value is added up from the
  cleaned player-match lines, never from a Player page mart, and compared against the marts by the
  existing tests. The description of the Squad answer key in schema.yml reads "a Squad".
refs: "#256, #136"

scope_paths:
  - dbt_project/seeds/player_window_answer_key.csv
  - dbt_project/seeds/player_page_answer_key.csv
  - dbt_project/seeds/schema.yml
  - .claude/task/256-player-order-value-tests/contract.md
  - .claude/task/256-player-order-value-tests/review.md
  - .claude/task/256-player-order-value-tests/review_input.patch

depends_on:
  - none: the change stands alone
shared_files:
  - none: no design baseline, chart manifest or chart pin changes

decisions_taken: >
  The coordinating session's message of 2026-11-22 rules the work: add the missing value tests on
  the window and Squad keys. The metric order is not changed here: the catalogue on main owns it.
  The Squad rank stays direction-blind: #136 approved the Squad comparison as a player's role in
  the squad, not quality (approved in chat, 2026-11-01), and the new Squad rows state it.
  goals_against_per90 and ball_actions_player have no Squad or window-count row to test, because
  the Squad serves outfield rates and the window model serves ball actions per 90 only. No new
  dependency, no cost. Round 4 on this removal delta is approved in chat, 2026-11-23.

decisions_reserved:
  - "none: every added value is a count computed from the data"

approved_design:
  - "none: no page layout changes; the rows test values the marts already serve"

done_when:
  - "`.venv/Scripts/dbt.exe parse --project-dir dbt_project` passes."
  - "On the prod marts, each added answer-key row equals the model's value: assert_player_window_answer_key and assert_player_page_answer_key return no row in the merge request's data build."

amendments: (none)
