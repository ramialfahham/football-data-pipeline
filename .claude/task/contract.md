# Task contract — researched line-ups, batch 1: Premier League

objective: >
  fixture_lineup_corrections gains the researched line-ups of the Premier League matches of the
  2025 and 2026 seasons on the research list: both team sheets of each match, every player with
  the provider's id, starter or bench, the minutes on and off, whom each substitute replaced and
  the formation, from the official premierleague.com match page. A match the official page cannot
  complete stays out and is listed in the MR.

refs: >
  #176 (https://gitlab.com/rami.al-fahham/football-data-pipeline/-/work_items/176): the research
  order and sources. The pilot plan: approved in chat, 2026-10-12.

scope_paths:
  - dbt_project/seeds/fixture_lineup_corrections.csv
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md

impact_map: >
  writers: the seed rows, written by hand from the official match pages; base_apif__lineups applies
  them, replacing the provider's sheets of each listed match. Nothing else changes.
  downstream: base_apif__lineups, fct_fixture_lineup, base_apif__players, dim_player and every
  reader of fct_fixture_lineup: mart_player_fixture_stats and mart_competition_fixtures, whose
  listed matches turn from not_available to researched.
  layer_rules: the seed is configuration applied in base, on the existing pattern.
  deploy_order: dbt seed precedes the models in data:build:main and fdp-nightly.
  blast_radius: only the listed matches: their line-ups, formations and lineup_state; the research
  list loses them.

decisions_taken: >
  The research order, the sources and the Premier League pilot: approved in chat, 2026-10-12. A
  missing outgoing player is the player of the substitute's team, a starter or a substitute who
  came on earlier, whom the official page shows going off at the substitution's minute; where two
  went off in that minute, the page's commentary names the pair: approved in chat, 2026-10-12.
  Half-time substitutions keep the provider's 46', where the official page shows 45', so every
  match shares one convention: approved in chat, 2026-10-12. Where the official page gives a
  substitution a different minute from the provider, the rows carry the official minute. Player
  ids are the provider's; where the provider gives one player two ids, the rows use the team
  sheet's id that the official sheet confirms by shirt number; a match whose official sheet names
  a player without a provider id stays out.

  THRESHOLD DECLARATIONS: NEW MECHANISM: none; rows in the existing seed. RECURRING COST: none
  measurable; 999 seed rows.

decisions_reserved:
  - The next leagues and batches.
  - The older seasons.

done_when:
  - dbt parse passes; the seed's tests pass.
  - The branch's base_apif__lineups on prod data turns every listed match researched, assert_lineup_researched_matches_hold returns no rows, and the research list loses exactly those matches.
  - data:build:mr is green on the MR.

amendments: >
  Review round 1 found the outgoing-player rule written as "the starter", while in 25 of the 26
  researched substitutions the player who went off had come on earlier; the CPO corrected the
  wording and decided the half-time minute convention, both in chat, 2026-10-12.
