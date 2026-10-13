# Task contract — researched line-ups, batch 4: Argentina's Liga Profesional

objective: >
  fixture_lineup_corrections gains the researched line-ups of the Liga Profesional matches of the
  2026 season on the research list: both team sheets of each match, every player with the
  provider's id, starter or bench, the minutes on and off and whom each substitute replaced, from
  the league's official match sheet on ligaprofesional.ar. A match the official sheet cannot
  complete stays out and is listed in the MR.

refs: >
  #176 (https://gitlab.com/rami.al-fahham/football-data-pipeline/-/work_items/176): the research
  order, the sources and the id rule. Argentina as the next league: approved in chat, 2026-10-13.

scope_paths:
  - dbt_project/seeds/fixture_lineup_corrections.csv
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md

impact_map: >
  writers: the seed rows, built from the official match sheets and the provider's sheets;
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
  The research order (current season only) and Argentina as the batch: approved in chat,
  2026-10-13. As in batches 1 to 3 (approved in chat, 2026-10-12): half-time substitutions keep
  the provider's 46', where the official sheet stamps them 45'; where the official sheet gives a
  substitution a different minute or pairing from the provider, the rows carry the official one,
  because the seed replaces the provider's sheets with the official record. Substitutions in the
  breaks of extra time keep the provider's 91' and 106' where the official sheet stamps them 90'
  and 105', read as the half-time rule, as the MLS batch did for its one break substitution.
  Player ids are the
  provider's: a player the official sheet names and the provider's sheet leaves out takes the id
  the provider gives him at that club in that season, on its squad list or on its own team sheet
  of another match (approved in chat, 2026-10-13); with no such id the match stays out. The
  official sheet shows neither formations nor unused substitutes, so the rows keep the
  provider's formations, pitch positions and unused substitutes.

  THRESHOLD DECLARATIONS: NEW MECHANISM: none; rows in the existing seed. RECURRING COST: none
  measurable; 1,185 seed rows.

decisions_reserved:
  - The next leagues and batches.
  - The previous season, #215.
  - The provider's garbled player names in its own data (a separate data-quality defect).

done_when:
  - dbt parse passes; the seed's tests pass.
  - The branch's base_apif__lineups on prod data turns every listed match researched, assert_lineup_researched_matches_hold returns no rows, and the research list loses exactly those matches.
  - data:build:mr is green on the MR.

amendments: >
  none.
