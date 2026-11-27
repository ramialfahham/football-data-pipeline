# Task contract — kick-off days and orders for the fan's time zone (part 1 of 3)

objective: >
  Issue #362, part 1 of 3: the warehouse and the export serve what pages in the fan's time zone
  need. mart_match_days serves each match on every day a time zone puts it on, both match orders
  run by the kick-off instant, and a team's next match carries its place by kick-off.

refs: >
  #362 (header design approved in chat, 27 Nov 2026, recorded on the issue: kick-off times are
  shown in the fan's time zone). Part 2 is the design checks, part 3 the site.

scope_paths:
  - .claude/task/362-a-zone-days/
  - dbt_project/models/5_marts/shared/mart_match_days.sql
  - dbt_project/models/5_marts/shared/mart_competition_fixtures.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/tests/assert_mart_match_days_is_the_matches_page_reach.sql
  - dbt_project/tests/assert_mart_match_days_serves_every_zone_day.sql
  - dbt_project/tests/assert_competition_fixtures_orders_follow_the_kickoff.sql
  - scripts/export_site_data.py
  - tests/test_export_matches.py
  - tests/test_export_site_data.py
  - tests/test_kickoff_clock_146.py
  - tests/test_no_decision_history_in_code.py

impact_map: >
  writers: mart_match_days and mart_competition_fixtures. mart_match_days changes grain from
  fixture_sk to (match_day, fixture_sk): a match is served on its UTC date, flagged is_utc_day, and
  on the dates of its kick-off 12 hours earlier and 14 hours later; every such day is a page day;
  day_row_order runs by kick-off over a day's own and neighbouring rows; is_opening_day is the
  first day from the build day on with a match on its UTC date. mart_competition_fixtures'
  fixture_order runs each round by the kick-off instant instead of the venue's clock, and the
  model adds kickoff_order, each match's place among all matches by kick-off instant.
  scripts/export_site_data.py carries is_utc_day on a Matches day's rows and kickoff_order on a
  team's next match; it selects and orders nothing.
  downstream: `dbt ls --select mart_match_days+ mart_competition_fixtures+ --resource-type model
  --output name` lists mart_competition_fixtures, mart_competition_research_list, mart_match_days,
  mart_player_index, mart_team_competitions, mart_team_index. Only the export reads fixture_order,
  kickoff_order or mart_match_days.
  layer_rules: the zone days and both orders are served by the marts; the export groups and
  formats only. check_layer_contract applies.
  deploy_order: the nightly builds the new marts after the merge. The site on main does not read
  is_utc_day, so a full export built into today's site would list a neighbouring day's matches
  under a day, and its match lists head dates on the venue's clock, so the instant order could put
  those headings out of date order or repeat one. No scheduled job deploys the site (Cloud
  Scheduler holds fdp-nightly and fdp-freshness only, read 27 Nov 2026) and deploy:site-v2 is
  manual. The merge changes the site image's inputs, so deploy:site-image would put the new export
  with the old site into the fdp-site job: fdp-site is neither run nor scheduled, and the site is
  not deployed, until part 3 has merged.
  blast_radius: on prod data the new mart_match_days holds 1,669 rows, 823 of them on a UTC date,
  over 84 days (65 before). fixture_order changes only the order of rows inside a round. The
  committed site sample is untouched.

approved_design:
  - matches: #130
  - match: #132

depends_on:
  - none: no MR is open; the work starts from main

shared_files:
  - none: no design baseline or chart screenshot changes in this part

decisions_taken: >
  Kick-off times are shown in the fan's time zone on every page, the Matches page included: the
  zone rule approved in chat, 27 Nov 2026, recorded on #362, with the coordinating session's call
  on the Matches page. Serving the zone days and the kick-off order from the marts is an
  engineering call under the consumption-layer rule (dbt_project/docs/layering.md). The Matches
  page gains a day that only a neighbouring day's match reaches; what it shows is part 3. No new
  mechanism and no recurring cost: the same two models, built by the same nightly. The header work
  is split into three MRs because one branch needed four reviewers and a branch may need two
  (working_agreement section 2).

decisions_reserved:
  - none: the rule is approved on #362; questions go to the coordinating session.

done_when:
  - python scripts/ci_local.py --mr is green.
  - Both mart tests of the zone days and the order test return no row, run read-only on prod data.

amendments:
  - The rewritten test header removes one flagged line, so the pin of decision history in code moves down and its test file is in scope. No decision is added.
  - The next match reads kickoff_order strictly, so the clock test's row carries one and its file is in scope. No decision is added.
