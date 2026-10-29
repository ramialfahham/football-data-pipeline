# Task contract — the official league table at every kick-off

objective: >
  Goals, points, standings and results are exact at all times. The Team page's "Season before"
  (#235) shows last season's points and place on the day the team played its Nth match. A new
  intermediate rebuilds each domestic league's official table at every kick-off: table points are
  the points won less the deductions in effect that day, and the order follows the league's own
  regulation for that season, from a new rule seed with its official sources. A tie the results
  cannot settle has no place. The rebuilt table must equal every published table the provider
  gave us, as an error test, so a wrong value fails the build.

refs: >
  #235 (the Team page build). The plan, approved in chat, 2026-10-29: dated deduction steps,
  each league's tie-break rules from its regulation, table points for points_this_season and
  points_prev_season, the checks as errors against the final tables and every published
  snapshot, and the removal of the sentence that allowed a computed position from the metric
  rules. points_rank's description "The team's place in its league table, with teams level on
  points ordered by the league's own rules." and interpretation "League position - 1 = top of the
  table; the place in the official table at that point of the season": approved in chat,
  2026-10-29.

scope_paths:
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season__table_by_time.sql
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season__position_by_match.sql
  - dbt_project/models/4_intermediate/domestic_league/team_season/*.yml
  - dbt_project/models/4_intermediate/shared/int_team_profile__yoy.sql
  - dbt_project/models/4_intermediate/shared/int_standings__section_kinds.sql
  - dbt_project/models/4_intermediate/shared/*.yml
  - dbt_project/models/5_marts/shared/mart_team_profile.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/models/docs/*.md
  - dbt_project/seeds/standings_points_adjustments.csv
  - dbt_project/seeds/league_tiebreak_rules.csv
  - dbt_project/seeds/standings_temporary_results.csv
  - dbt_project/seeds/schema.yml
  - dbt_project/seeds/metric_catalogue.csv
  - dbt_project/seeds/metric_map.csv
  - dbt_project/tests/assert_*.sql
  - tests/test_*.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md

impact_map: >
  writers: int_team_season__table_by_time replaces int_team_season__position_by_match;
  standings_points_adjustments gains dated steps; league_tiebreak_rules is new;
  int_team_profile__yoy reads the rebuilt table for points_this_season, points_prev_season,
  points_delta_yoy and points_rank_prev_season, and mart_team_profile carries them. downstream:
  the readers of int_team_profile__yoy (listed by dbt ls in the evidence). layer_rules: computed in
  the warehouse; no export change. deploy_order: the MR data build. blast_radius: the yoy points
  and place columns, two seeds, the tests on the table.

approved_design:
  - team: #134

acceptance_criteria:
  - "standings_points_adjustments holds one row per deduction step with the date it took effect and its official source; tested unique per team, section and date, every step changing the points and dated."
  - "league_tiebreak_rules holds each league's ordered criteria per phase and first season, each with its official regulation as source, from a closed list of criteria and conditions tested as accepted values."
  - "int_team_season__table_by_time holds every ranked league-season's table at every kick-off: played, table points, goal difference, goals and the place by the league's rules, empty where teams stay level at a criterion the results cannot settle."
  - "int_team_profile__yoy's points_this_season, points_prev_season, points_delta_yoy and points_rank_prev_season read the rebuilt table on the day of the team's Nth match."
  - "An error test compares the rebuilt place and points with every published table the provider gave us, wherever the published played counts match the rebuilt ones, and fails for a ranked league-season with no comparable published table; the two warning tests it replaces are removed."
  - "The metric rules no longer hold the sentence that allowed a computed position."

decisions_taken: >
  The plan, approved in chat, 2026-10-29. Readings: "the same point" is the day of the team's Nth
  match, so the table counts every match kicked off by then, other teams' games in hand included;
  the published tables are the provider's daily snapshots, each covering every season the league
  configures, so they hold every past season's final table and this season's matchdays; a
  published table where a team's played count differs from the rebuilt one is not comparable
  (the provider had not yet counted a match) and is left out, with every ranked league-season
  needing at least one comparable table. No new dependency; the recurring cost is measured on the
  MR data build and put to the CPO before the merge.

decisions_reserved:
  - Any catalogue description text beyond points_rank's approved one.

done_when:
  - dbt parse, SQLFluff on every changed model, a dry run of each against prod, pytest and the offline gates pass.
  - The MR data build passes with every table test as an error; its added bytes are measured and put to the CPO.
  - Reviewers per review_routing.json pass.

amendments: >
  int_standings__section_kinds.sql enters scope: its header names the model this replaces. A
  deduction that was annulled (Napoli 2020-21) nets to zero, so the seed's test checks that every
  step changes the points and carries a date, not a net above zero. The fan-question test's
  question 2 asked for points against the same point last season through the catalogue map;
  those are now table points, outside the catalogue, so it asks for points won in the last five
  matches instead. Round 1 of the review: the published-table test leaves out a published table
  with a deduction step dated after the rebuilt table's kick-off; the previous season's place is
  read from single-table seasons only, one row per team; the second head-to-head pass groups by
  the first pass's criteria as the rule applies them; a test requires every rule version to end
  in undecidable. Those three are technical fixes inside the approved plan: two tables that hold
  different deductions by construction are not compared, since comparing them fails a correct
  table, and the previous season's final place exists only where that season had one table per
  team. A result the official table held for a time and that was later annulled (Serie A 2020-21:
  a 3-0 Juventus win over Napoli awarded on 14 Oct 2020, annulled on 22 Dec 2020 and the match
  replayed) is recorded with its dates and official sources in a new seed,
  standings_temporary_results, and the rebuilt table counts it only between those dates; approved
  in chat, 2026-10-29. The approved plan states the reading of the metric rules' "taken as
  published, never computed": "A rebuilt table is the published table at that match, and the
  tests below prove it equal."
