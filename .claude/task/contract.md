# Task contract — researched line-ups, batch 5: the elite pool and the World Cup

objective: >
  fixture_lineup_corrections gains the researched line-ups of the current-season matches on the
  research list of the elite pool's leagues (La Liga, Serie A, Ligue 1, Liga Portugal, Eredivisie)
  and of the World Cup 2026: both team sheets of each match, every player with the provider's id,
  starter or bench, the minutes on and off and whom each substitute replaced, from each
  competition's official match record (laliga.com, legaseriea.it, ligue1.com, ligaportugal.pt,
  eredivisie.nl, fifa.com). A match the official record cannot complete stays out and is listed in
  the MR.

refs: >
  #176 (https://gitlab.com/rami.al-fahham/football-data-pipeline/-/work_items/176): the research
  order, the sources and the id rule. The elite pool and the World Cup as the competitions
  researched now, the rest parked in #216: approved in chat, 2026-10-13.

scope_paths:
  - dbt_project/seeds/fixture_lineup_corrections.csv
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md

impact_map: >
  writers: the seed rows, built from the official match records and the provider's sheets;
  base_apif__lineups applies them, replacing the provider's sheets of each listed match. Nothing
  else changes.
  downstream: base_apif__lineups, fct_fixture_lineup, base_apif__players, dim_player and every
  reader of fct_fixture_lineup: mart_player_fixture_stats and mart_competition_fixtures, whose
  listed matches turn from not_available to researched.
  layer_rules: the seed is configuration applied in base, on the existing pattern.
  deploy_order: dbt seed precedes the models in data:build:main and fdp-nightly.
  blast_radius: only the listed matches: their line-ups, formations and lineup_state; the research
  list loses them.

decisions_taken: >
  The elite pool and the World Cup researched now, the rest of the current season parked in #216:
  approved in chat, 2026-10-13. As in batches 1 to 4 (approved in chat, 2026-10-12 and
  2026-10-13): half-time substitutions keep the provider's 46' where the official record gives
  them no minute or 45'; where the official record gives a substitution a different minute or
  pairing from the provider, the rows carry the official one, because the seed replaces the
  provider's sheets with the official record; where the official record writes minutes without
  added time and the provider's minute is the same minute with added time, the rows keep the
  provider's added time, the two agreeing. Player ids are the provider's: a player the official
  record names and the provider's sheet leaves out takes the id the provider gives him at that
  club in that season, on its squad list or on its own team sheet of another match; with no such
  id the match stays out. Formations and pitch positions are the provider's, as for MLS; where
  the provider has no formation for a team the row takes the official one: approved in chat,
  2026-10-13.

  THRESHOLD DECLARATIONS: NEW MECHANISM: none; rows in the existing seed. RECURRING COST: none
  measurable; 1,056 seed rows.

decisions_reserved:
  - The competitions parked in #216 and the previous season, #215.
  - The provider's garbled player names in its own data (a separate data-quality defect).

done_when:
  - dbt parse passes; the seed's tests pass.
  - The branch's base_apif__lineups on prod data turns every listed match researched, assert_lineup_researched_matches_hold returns no rows, and the research list loses exactly those matches.
  - data:build:mr is green on the MR.

amendments: >
  none.
