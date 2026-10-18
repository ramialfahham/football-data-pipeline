# Verification — Next matches: the warehouse serves the competition order

No file under `site_v2/src/` changes. This MR is the warehouse half of the one criterion; the page
half, Home rendering the served order, is built and demonstrated in the next MR of #219.

criteria_demonstrated:
  - Served: `mart_next_matchday.competition_order` is the dense rank of each competition by first matchday date, region rank, earliest kick-off, league_code; `dbt parse` passes and sqlfluff (full rule set) passes on the model and its test.
  - Tested: `assert_mart_next_matchday_competition_order_follows_the_key` recomputes the order from the mart's rows and the two seeds and fails on any competition with two orders, a shared order or a different place; CI `data:build:mr` runs it with the model's not_null test.
