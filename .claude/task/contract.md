# Task contract — researched line-ups of the 26 matches behind the blank squads

objective: >
  fixture_lineup_corrections gains the researched line-ups of 26 of the 30 matches behind the 41
  blank squads: both team sheets of each match, every player with the provider's id, starter or
  bench, the minutes on and off and whom each substitute replaced, from the competition's official
  match record (resultados.rfef.es, uefa.com, veikkausliiga.com, kleague.com). Their sheets then
  feed base_apif__fixture_players_from_lineups, so the clubs' players gain these matches.

refs: >
  #176 (https://gitlab.com/rami.al-fahham/football-data-pipeline/-/work_items/176): the sources, the
  order and the id rule. #256 (https://gitlab.com/rami.al-fahham/football-data-pipeline/-/work_items/256):
  the squads a match with no player rows blanks. Researching the 30 matches: approved in chat,
  2026-11-06.

scope_paths:
  - dbt_project/seeds/fixture_lineup_corrections.csv
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md

impact_map: >
  writers: the seed rows, built from the official match records and the provider's sheets;
  base_apif__lineups applies them, replacing the provider's sheets of each listed match, and
  base_apif__fixture_players reads their player ids. Nothing else changes.
  downstream: `dbt ls --select fixture_lineup_corrections+ --resource-type model` starts at
  base_apif__fixture_players and base_apif__lineups, then base_apif__fixture_players_from_lineups,
  fct_fixture_lineup, fct_fixture_player_stats, base_apif__players, dim_player, and every reader of
  those: the int_legs models, the player and team season and window models,
  mart_player_fixture_stats and mart_competition_fixtures.
  layer_rules: the seed is configuration applied in base, on the existing pattern.
  deploy_order: dbt seed precedes the models in data:build:main and fdp-nightly.
  blast_radius: only the 26 listed matches: their line-ups, formations and lineup_state turn from
  not_available to researched, and the 52 team matches gain 1,089 player rows in
  base_apif__fixture_players_from_lineups, so those players' appearances, minutes, goals, assists
  and cards count these matches. The research list loses them.

decisions_taken: >
  Researching the 30 matches, an exception to the parking in #216: approved in chat, 2026-11-06.
  The rules of batches 1 to 5 apply as written: the official minute and pairing where the provider
  differs, half-time substitutions keep the provider's 46', formations and pitch positions are the
  provider's, and where it has none the row takes the official one or stays blank. Player ids are
  the provider's. A match the official record cannot complete stays out.

  Every row was read before research stopped on 2026-11-06 (#176 note 4181292451). 17 of the 26
  matches come from sites that note stops: uefa.com 11, resultados.rfef.es 6. Note 4181311140 keeps
  researched rows in use on main and in the card research and does not name these line-ups, so the
  MR head declares it and the merge decides.

  THRESHOLD DECLARATIONS: NEW MECHANISM: none; rows in the existing seed. RECURRING COST: none
  measurable; 1,089 seed rows.

decisions_reserved:
  - The four matches of the 30 left out, and the rest of #216.
  - Whether line-up research resumes, and on which sites (#176, #262).
  - The written permission of the leagues and the legal check before go-live (#176 note 4181311140).
  - Sevilla's nameless 38' yellow in 1645578 and the second id of N. Pinto in 1623421: card research and #260, not this MR.

done_when:
  - dbt parse passes; the seed's tests pass.
  - The branch's base_apif__lineups on prod data turns every listed match researched, assert_lineup_researched_matches_hold and assert_players_from_lineups_goals_add_up return no rows, and the research list loses exactly those matches.
  - data:build:mr is green on the MR.

amendments: >
  none.
