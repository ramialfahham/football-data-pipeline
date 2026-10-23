# Task contract — the goals of CAF match 1639347

objective: >
  CAF Champions League match 1639347, Young Africans 4–1 CFFA (second preliminary round, second
  leg), serves its five goals from fixture_goal_corrections, each sourced, so its goals add up to
  its score; assert_mart_competition_fixtures_goals_add_up and assert_result_corrections_applied
  pass and mart_match_days builds again in the nightly.

refs: >
  #232, the match's goals
  (https://gitlab.com/rami.al-fahham/football-data-pipeline/-/work_items/232), fix and plan
  approved in chat, 2026-10-23.

scope_paths:
  - dbt_project/seeds/fixture_goal_corrections.csv
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md

impact_map: >
  writers: the seed fixture_goal_corrections, read by base_apif__fixture_events.
  downstream: base_apif__fixture_events and every model built from it (dbt ls --select
  fixture_goal_corrections+), among them fct_fixture_event, mart_competition_fixtures and
  mart_match_days; only the rows of fixture 1639347 change.
  layer_rules: a seed row per goal, applied in base as the seed's description states; no model
  changes.
  deploy_order: none; the nightly rebuilds prod from main.
  blast_radius: one match's goals in every mart that serves goals; mart_match_days, skipped by the
  nightly while the goals test failed, builds again.

approved_design:
  - none: no page output changes

acceptance_criteria:
  - "fixture_goal_corrections holds five rows for fixture 1639347 in match order, each with its team, scorer, minute, event detail, source kind, source URLs and note."
  - "In the MR's data build, assert_mart_competition_fixtures_goals_add_up and assert_result_corrections_applied pass."
  - "In the MR's data build, mart_match_days builds and assert_mart_match_days_is_the_matches_page_reach passes."

decisions_taken: >
  Approved in chat, 2026-10-23: the five goals as CAF's match report and two Malagasy match reports
  give them. Reading of the seed's rule: the four Young Africans goals are official, from CAF's
  match report; CFFA's goal is match_reports, because CAF's report names no scorer and Newsmada and
  Midi Madagasikara both name Fitahantsoa Albertini. Its minute is CAF's. No new dependency, no
  recurring cost.

decisions_reserved: (none)

done_when:
  - dbt parse passes.
  - The full pytest suite and the offline gates pass.
  - Reviewers per review_routing.json pass.
  - data:build:mr passes and the prod comparison of the match's served goals goes to the CPO.

amendments: (none)
