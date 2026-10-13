# Task contract — researched line-ups, batch 3: MLS

objective: >
  fixture_lineup_corrections gains the researched line-ups of the MLS matches of the 2025 and 2026
  seasons on the research list: both team sheets of each match, every player with the provider's
  id, starter or bench, the minutes on and off and whom each substitute replaced, from the league's
  official match data shown on the mlssoccer.com line-up and match feed pages. A match the official
  data cannot complete stays out and is listed in the MR.

refs: >
  #176 (https://gitlab.com/rami.al-fahham/football-data-pipeline/-/work_items/176): the research
  order and sources. MLS as the next league: approved in chat, 2026-10-12.

scope_paths:
  - dbt_project/seeds/fixture_lineup_corrections.csv
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md

impact_map: >
  writers: the seed rows, built from the official match data and the provider's sheets;
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
  The research order, the sources and the MLS batch: approved in chat, 2026-10-12. As in batches 1
  and 2 (approved in chat, 2026-10-12): half-time substitutions keep the provider's 46', where the
  official data gives them no minute; where the official data gives a substitution a different
  minute or pairing from the provider, the rows carry the official one, because the seed replaces
  the provider's sheets with the official record. Player ids are the provider's: where the
  provider's sheet leaves out a player the official sheet names, the row takes the id the
  provider's squad list gives that player at that club in that season; a match whose official
  sheet names a player the provider holds no confirmable id for stays out. MLS formations and pitch
  positions are the provider's, because the official data writes formations in another notation
  and lacks some: approved in chat, 2026-10-12.

  THRESHOLD DECLARATIONS: NEW MECHANISM: none; rows in the existing seed. RECURRING COST: none
  measurable; 2,547 seed rows.

  Austin-LAFC (2025 playoffs) stays out: the provider's player statistics put a player the
  official sheet has at Austin under LAFC, and the player-stats mart takes the team from the
  statistics first; it returns once a separate fix makes a checked line-up's team win: approved in
  chat, 2026-10-12.

decisions_reserved:
  - The next leagues and batches.
  - The older seasons.
  - The provider's garbled player names in its own data (a separate data-quality defect).

done_when:
  - dbt parse passes; the seed's tests pass.
  - The branch's base_apif__lineups on prod data turns every listed match researched, assert_lineup_researched_matches_hold returns no rows, and the research list loses exactly those matches.
  - data:build:mr is green on the MR.

amendments: >
  none.
