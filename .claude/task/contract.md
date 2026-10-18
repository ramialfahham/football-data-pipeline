# Task contract — Next matches: the warehouse serves the competition order

objective: >
  Home's Next matches block orders its competitions in the page code (orderUpcomingGroups), which
  layering.md forbids. mart_next_matchday gains competition_order, the ruled order of the
  competitions, so the Home rebuild (#219) can render the order it is served. This is the
  warehouse half of #219; the export and the page follow in the next MR, once this column is built.

refs: >
  #219, the Home build (https://gitlab.com/rami.al-fahham/football-data-pipeline/-/work_items/219);
  #127, Home's approved design, "Order of competitions". Plan approved in chat, 2026-10-18.

scope_paths:
  - dbt_project/models/5_marts/shared/mart_next_matchday.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/tests/assert_mart_next_matchday_competition_order_follows_the_key.sql
  - dbt_project/docs/layering.md
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md

impact_map: >
  writers: mart_next_matchday.sql is the only writer of the mart; it gains one column and loses
  nothing.
  downstream: `dbt ls --resource-type model --select mart_next_matchday+ --output name` →
  mart_competition_fixtures, mart_match_days, mart_next_matchday. Both readers name the columns
  they take from it (no select *), so the new column reaches neither. Outside dbt the one reader
  is scripts/export_site_data.py (fetch_landing_payload), which names its columns and is unchanged
  in this MR.
  layer_rules: an ordering is the warehouse's (layering.md, Consumption layer, "ALL ranking and
  ordering"); the column is a mart column from fct_fixture and two seeds; no partition_by or
  cluster_by.
  deploy_order: additive column; the deployed export does not read it, so nothing breaks before
  or after merge. The 04:00 UTC nightly builds it; the next MR's export reads it only after that.
  blast_radius: one new column on mart_next_matchday; no existing value of any mart changes.

approved_design:
  - home: #127

acceptance_criteria:
  - "The order of the competitions in Next matches is served by the warehouse; the page applies no order of its own."

decisions_taken: >
  Plan approved in chat, 2026-10-18: the column is named competition_order and is the dense rank
  of each competition by the key #127 rules (the day its matchday starts, then region rank, then
  its earliest kick-off, then league_code). The page half of the acceptance criterion, Home
  rendering the served order, is built in the next MR of #219 and demonstrated there. No new
  mechanism, no recurring cost: one column on a nightly-built table.

decisions_reserved:
  - none: the order key is ruled on #127 and the column name was approved with the plan.

done_when:
  - dbt parse passes.
  - sqlfluff lint of the changed model and the new test passes, full rule set, from the repo root.
  - The offline gates (FAST_GATES) and the full pytest suite pass.
  - Reviewers per review_routing.json pass.
  - CI data:build:mr builds the model and passes its tests.

amendments:
  - 2026-10-18: + dbt_project/docs/layering.md — authority: the standing rule that a rule's owning document is edited in the same MR (working_agreement.md §11); content: its mart_next_matchday row stops saying the mart is not ordered.
