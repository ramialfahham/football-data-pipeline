# Task contract — a player's team in a match follows the checked line-up: proof and one goal correction

objective: >
  Issue 213. The line-up already decides a player's team in a confirmed or researched match
  (commit 615de683). This task pins that guarantee with a singular test on the mart the pages read,
  and corrects the one goal a page shows with an assist by a player of the other team's sheet:
  Bayern-Gladbach, Bundesliga, 13 Jun 2020 (fixture 209184), from the league's official match data.

refs: >
  Issue 213; go-live gate issue 290. Route set by the coordinating session.

scope_paths:
  - dbt_project/tests/assert_player_fixture_team_follows_lineup.sql
  - dbt_project/seeds/fixture_goal_corrections.csv
  - .claude/task/213-player-team-lineup/contract.md
  - .claude/task/213-player-team-lineup/review.md
  - .claude/task/213-player-team-lineup/review_input.patch

approved_design:
  - none: no page output changes beyond the corrected goals of fixture 209184

depends_on:
  - none: needs no open MR's code; it reads only models already on main

shared_files:
  - none: no design baseline, chart manifest or chart pin changes

impact_map: >
  writers: fixture_goal_corrections is read by base_apif__fixture_events only; the new test reads
  marts.mart_player_fixture_stats and core.fct_fixture_lineup and writes nothing but its failures.
  downstream: `dbt ls --select fixture_goal_corrections+ --resource-type model` lists every events,
  player, team and fixture model through to the marts (mart_competition_fixtures,
  mart_player_fixture_stats, mart_team_fixtures and 27 more), because the events feed them all.
  layer_rules: cleaning stays in base (the seed is applied in base_apif__fixture_events); the test
  reads marts and core only.
  deploy_order: a seed row and a test; no model changes, so nothing breaks between merge and the
  04:00 nightly.
  blast_radius: one match. Fixture 209184's goals become Zirkzee 26' with no assist, Pavard's own
  goal 37', and Goretzka 86' with Pavard's assist; before, the first goal read 16' with Gladbach's
  Hofmann as its assist. The stat lines of the four players are unchanged on prod (goals and
  assists already right). Measured in the MR by comparing ci_mr tables with prod.

decisions_taken: >
  The cleaning rule "Where a match's line-ups are researched, the researched sheet decides a player's
  team" and the Line-ups rules (a confirmed sheet fails when a stat line puts a player on the other
  team) are approved and already built; this task adds no rule. The goal row applies the approved
  goal-correction route (a match whose provider goal events are wrong takes its goals from sourced
  research, source_kind official). The new test is error severity: it holds a guarantee of our own
  code, and a failure means a fan sees a player at the wrong club. No new mechanism, no recurring cost.

decisions_reserved:
  - none: the 81 other matches whose goal minute contradicts the sheet are listed in the MR for the
    coordinating session to route; no generic rule is built for them here.

done_when:
  - assert_player_fixture_team_follows_lineup returns 0 rows on prod (read-only run of its SQL) and
    in data:build:mr.
  - assert_result_corrections_applied and assert_player_match_cleaning_answer_key pass in data:build:mr.
  - mart_competition_fixtures in the ci_mr dataset shows fixture 209184's goals as researched.
  - A read-only ci_mr vs prod comparison lists every player-match whose team changed, with the count.
  - python scripts/ci_local.py --mr is green.

amendments: (none)
