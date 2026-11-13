# Task contract — the nightly green and stable: three failing tests fixed at their root

objective: >
  Issue #262, first part: the three tests that failed the 11 and 12 Nov nightlies pass on the data
  that failed them, and the Chelsea failure no longer depends on the order competitions are
  ingested. A team's settled row is never one with no attributes when another of its rows has
  them; Peña Sport's researched goal names its scorer's id; a combined table of a league-season
  that sits beside its group tables is classified with the rankings the page already drops.

refs: >
  #262 (the CPO's principle note of 2026-11-11: a record that empties a filled field keeps the known
  value). The three routes were ruled by the coordinating session on 2026-11-12 after the read-only
  trace of the failing rows; the rest of the guard (players, identity changes held and listed) is a
  second MR.

scope_paths:
  - dbt_project/seeds/fixture_goal_corrections.csv
  - dbt_project/models/2_base/api_football/base_apif__teams_global.sql
  - dbt_project/models/2_base/api_football/base.yml
  - dbt_project/models/4_intermediate/shared/int_standings__section_kinds.sql
  - dbt_project/models/4_intermediate/shared/int_standings__section_kinds.yml
  - dbt_project/tests/assert_every_standings_section_has_a_table_kind.sql
  - dbt_project/tests/assert_standings_cross_group_rankings.sql
  - dbt_project/tests/assert_team_keeps_its_filled_row.sql
  - dbt_project/tests/assert_team_country_corrections_still_needed.sql
  - dbt_project/tests/assert_team_name_overrides_still_needed.sql
  - .claude/task/262-nightly-green/contract.md
  - .claude/task/262-nightly-green/review.md
  - .claude/task/262-nightly-green/review_input.patch

impact_map: >
  writers: dbt only; no ingestion or export change. fixture_goal_corrections is read by
  base_apif__fixture_events; base_apif__teams_global by dim_team; int_standings__section_kinds by
  mart_standings, int_team_season__table_state and int_team_season__standings_primary.
  lineage: `dbt ls --resource-type model --output name --select base_apif__teams_global+
  int_standings__section_kinds+ fixture_goal_corrections+` returns 90 models, among them
  base_apif__fixture_events, base_apif__fixture_players_from_lineups, base_apif__lineups,
  base_apif__players, dim_team, dim_player, fct_fixture_event, fct_fixture_lineup,
  fct_fixture_player_stats, int_standings__section_kinds, int_team_season__standings_primary,
  int_team_season__table_state, mart_standings, mart_team_index, mart_team_profile,
  mart_team_competitions, mart_competition_fixtures, mart_player_fixture_stats,
  mart_player_profile, mart_leaderboards and every other team and player mart.
  consumption: the export reads the same columns. mart_standings' table_kind for one section
  changes from league to ranking, and the competition page drops a ranking
  (site_v2/src/lib/competitionPayload.mjs), as it did before 2026-11-12.
  ci_layer_rules: scripts/check_layer_contract.py, scripts/check_description_hygiene.py.
  deploy_order: one merge; the nightly rebuilds every model. No backfill.
  blast_radius: measured on prod 2026-11-12. The teams rule changes the settled row of 5 teams
  whose latest row has no attributes and another row has them (1538, 1551, 225, 4460, 1537); Chelsea
  (49) is on its filled row today by ingest order and stays on one. The seed cell gives Peña Sport's
  goal in fixture 1644366 to player 576050, so its 21 line-up rows get their goals. The section rule
  reclassifies one section, APD 2026 "Liga Profesional Argentina". Exact differences come from the
  MR build compared with prod.

approved_design:
  - none: the page change is the existing rule that a ranking is never shown, applied to one more section, and five teams' empty attributes filled from their own provider rows

decisions_taken: >
  Ruled by the coordinating session on 2026-11-12. (1) Player 576050 scored Peña Sport's goal in
  fixture 1644366: he stands on the confirmed sheet as "J. Recalde", came on at 57', and the
  provider's own goal event at 65' names him; the RFEF sheet already in the seed row names Joaquín
  Recalde. (2) A section the patterns leave as a league, in a league-season with group or conference
  sections, whose every team also sits in one of those sections, combines them: it is a ranking.
  The rule is structural, never a league's name; the split-season pin keeps every real phase table
  out of the rankings and pins APD 2026 "Liga Profesional Argentina" as the one combined table.
  Showing the combined table is a later product question. (3) base_apif__teams_global settles each
  team on its latest row that has any provider attribute, and on its latest row only where none
  has. This is the approved #262 rule for teams. No new mechanism, no recurring cost.

decisions_reserved:
  - Whether the competition page shows Argentina's combined annual table (a later CPO product question).
  - The rest of the #262 guard (players; identity changes held and listed) is a second MR.

done_when:
  - dbt parse passes; sqlfluff lint passes on every changed model and test.
  - The full pytest suite passes.
  - The MR's data build passes, and the read-only comparison of its ci_mr tables with prod shows assert_players_from_lineups_goals_add_up, assert_every_standings_section_has_a_table_kind and not_null_mart_team_index_team_country passing on 2026-11-12 data.

amendments:
  - 2026-11-12: + dbt_project/tests/assert_team_country_corrections_still_needed.sql, dbt_project/tests/assert_team_name_overrides_still_needed.sql — authority: decision (3) of decisions_taken; both tests compare the seeds against the row base_apif__teams_global settles on, so they take its new order; content: that order, nothing else.
