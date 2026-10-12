# Task contract — researched line-ups, batch 2: Bundesliga and 2. Bundesliga

objective: >
  fixture_lineup_corrections gains the researched line-ups of the Bundesliga and 2. Bundesliga
  matches of the 2025 and 2026 seasons on the research list: both team sheets of each match, every
  player with the provider's id, starter or bench, the minutes on and off, whom each substitute
  replaced and the formation, from the official bundesliga.com line-up page and live ticker. A
  match the official pages cannot complete stays out and is listed in the MR.

refs: >
  #176 (https://gitlab.com/rami.al-fahham/football-data-pipeline/-/work_items/176): the research
  order and sources. The Bundesliga batch as the next league: approved in chat, 2026-10-12.

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
  The research order, the sources and the Bundesliga batch: approved in chat, 2026-10-12. As in
  batch 1 (approved in chat, 2026-10-12): a missing outgoing player is the player of the
  substitute's team, a starter or a substitute who came on earlier, whom the official ticker shows
  going off at the substitution's minute; half-time substitutions keep the provider's 46', where
  the official ticker stamps them with the break time (45' plus the minutes of the break); where
  the official ticker gives a substitution a different minute from the provider, the rows carry
  the official minute. Where the official ticker pairs a substitution differently from the
  provider, the rows carry the official pair, because the seed replaces the provider's sheets with
  the official record. Player ids are the provider's: where the provider's sheet leaves out a
  player the official sheet names, the row takes the id the provider's squad list gives that
  player at that club in that season; a match whose official sheet names a player the provider
  holds no confirmable id for stays out.

  THRESHOLD DECLARATIONS: NEW MECHANISM: none; rows in the existing seed. RECURRING COST: none
  measurable; 1,318 seed rows.

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
