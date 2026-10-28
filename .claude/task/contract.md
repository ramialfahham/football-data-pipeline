# Task contract — the Team page's Competitions block

objective: >
  The warehouse serves the Team page's Competitions block (#235, design #134): one row per team,
  competition and season on mart_team_competitions, with the team's standing in that
  competition's table, the round of its latest played match, and for a cup the round it reached
  with Through, Knocked out or Winners. Each round of the round_names seed says whether it is a
  table round, a final, a third-place match or another knockout round; int_knockout_ties decides
  each tie by the goals over its legs, then a shoot-out or an awarded result, so a two-legged tie
  and an FA Cup replay are read as the tie, not the leg. The export carries the rows on the team
  payload's featured season.

refs: >
  #235 (the build; its plan approved in chat, 2026-10-28: the Competitions block "for a cup, the
  furthest round and Through / Knocked out / Winners, decided by the tie, not the leg"); #134 (the
  Team page design, approved in chat, 2026-10-22 and 2026-10-28; its cup rule: winning a tie shows
  the next round and Through, losing shows that round and Knocked out, winning the final shows
  Final and Winners); #148 (the round names); #178 (who went through, for match rows, which this
  tie model serves later).

scope_paths:
  - dbt_project/seeds/round_names.csv
  - dbt_project/seeds/schema.yml
  - dbt_project/models/4_intermediate/shared/int_round_names.sql
  - dbt_project/models/4_intermediate/shared/int_round_names.yml
  - dbt_project/models/4_intermediate/shared/int_knockout_ties.sql
  - dbt_project/models/4_intermediate/shared/int_knockout_ties.yml
  - dbt_project/models/5_marts/shared/mart_team_competitions.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/tests/assert_*.sql
  - scripts/export_site_data.py
  - scripts/check_copy_gate.py
  - tests/test_export_site_data.py
  - tests/test_governance_hooks.py
  - tests/test_no_decision_history_in_code.py
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md

impact_map: >
  writers: the round_names seed (a stage_kind column), int_round_names (round_stage_kind), a new
  intermediate int_knockout_ties and a new mart mart_team_competitions. downstream: `dbt ls
  --select round_names+ int_knockout_ties+ mart_team_competitions+ --resource-type model` lists 7
  models: int_knockout_ties, int_round_names, mart_competition_fixtures, mart_competition_index,
  mart_match_days, mart_next_matchday, mart_team_competitions; the four existing marts select
  named columns of int_round_names and do not read the new one, and nothing reads the two new
  models but mart_team_competitions and the export. The export's team
  payload gains the competitions rows. layer_rules: the tie and the outcome are computed in the
  warehouse; the mart reads mart_competition_fixtures and mart_standings in its own layer for the
  round order and the tables; the export only selects. deploy_order: the MR data build; the
  committed samples are re-exported with the page's build. blast_radius: the seed's new column,
  the two new models and their tests, the team payload's new key.

approved_design:
  - team: #134

acceptance_criteria:
  - "Every round_names row has stage_kind table, final, placement or knockout (a round named by a matchday is a table round, a final pattern a final, a third-place pattern a placement match, every other a knockout round); int_round_names serves round_stage_kind, and assert_every_round_text_resolves still names every latest-season round."
  - "int_knockout_ties has one row per team and tie (competition, season, round of ties, the two teams) with its legs, the legs played, the goals for and against over the played legs, and won true or false once every leg is played and the tie is decided by goals, then by the last leg's shoot-out or award; a level tie without one is undecided (null), as an FA Cup draw before its replay; tests pin one winner per decided tie."
  - "mart_team_competitions has one row per (team_sk, league_code, season_api_year) the team has a fixture in: competition_type, the standing of its table section (the section named in its latest played round, else the one with the most matches), the latest played round (copy key, number, letter), the round reached (its latest round, a third-place match left out) with cup_status through, knocked_out or winners (winners only for a final outside a qualifying competition), null while a tie is being played or in a table round, and competition_order; tests pin the grain, the accepted statuses, winners only in a final, at most one winner per competition-season, and that a knocked-out team or a winner has no later fixture in that competition."
  - "The team payload's featured season carries its competitions rows in competition_order; pytest pins it."

decisions_taken: >
  The build plan approved in chat, 2026-10-28, #134's cup rule, and #134's block order (note of
  2026-10-20: "one list row per competition this season, domestic first (league, then cup), then
  international"). Readings: a round's kind sits on the round_names row that names it, a round
  named by a matchday ("Matchday", "Matchweek", "Week") being a table round, the final patterns a
  final and the third-place patterns a placement match, Veikkausliiga's European play-off final
  being a knockout round, since it decides a place in Europe and no title; a tie is the fixtures of one round of
  ties between the same two teams, and an FA Cup replay is its own round, so a draw is undecided
  until the replay decides; a team drawn into a later round's unplayed tie is through to that
  round; a third-place match is not the round reached, so a semi-final loser is knocked out in
  the semi-final; winners are the winners of a final, a cup's or a league's play-off final for
  its title (Liga MX, MLS), as #134's rule "winning the final shows Final and Winners" reads, a
  qualifying competition's final winner being through; the standing is the team's section named
  in its latest played round (an Apertura or Clausura), otherwise its section with the most
  matches played; the latest played round gives the league's "Matchday N"; in the block order
  the domestic super cup follows the cups and each group runs by its latest match first; the
  export carries the rows on the featured season only, the one the page shows. No new dependency; the
  recurring cost is measured on the MR data build and put to the CPO before the merge.

decisions_reserved:
  - Any wording, block or rule the Team page design does not hold; last season's position, the last five matches and the squad's appearances follow in their own MR.

done_when:
  - dbt parse, SQLFluff on every changed model, a dry run of each against prod, pytest, the copy gate and the offline gates pass.
  - The MR data build passes, including the new tests; its added bytes are measured and put to the CPO.
  - Reviewers per review_routing.json pass.

amendments: (none)
