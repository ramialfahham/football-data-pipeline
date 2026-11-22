# Task contract - a player whose records hold two real birth dates or nationalities has the value withheld, not the nightly stopped

objective: >
  Issue #262, box "Only a check that catches a defect in our own code stops the nightly." The test
  assert_player_bio_conflicts_settled returns a player whose tied records hold two real birth dates
  (or two real nationalities) and who has no row in player_bio_corrections, and its error severity
  stops the nightly on a provider input. base_apif__players now withholds the value: it is blank
  and flagged (birth_date_needs_research, nationality_needs_research) until a correction row
  settles it. The test stays at error severity and proves the value is withheld, against a conflict
  it derives from the staged records itself, never from the flag. assert_identity_fields_never_blanked
  exempts the same derived conflicts, so over-flagging still fails it. A new warn test lists the
  withheld players: a player is no match, so he is not a row of mart_competition_research_list.

refs: >
  #262 What exactly / How (approved in chat, 15 Nov 2026). Part of the three provider checks that
  move from stopping the nightly to withholding; this one is the smallest of them.

depends_on:
  - none: glab mr list shows no open merge request; every file this change edits is on gitlab/main

shared_files:
  - none: no design baseline, chart manifest or chart pin is changed

scope_paths:
  - dbt_project/macros/withheld_when_conflicting.sql
  - dbt_project/macros/players_with_conflicting_bio.sql
  - dbt_project/models/2_base/api_football/base_apif__players.sql
  - dbt_project/models/2_base/api_football/base.yml
  - dbt_project/models/docs/cleaning_rules.md
  - dbt_project/tests/assert_player_bio_conflicts_settled.sql
  - dbt_project/tests/assert_identity_fields_never_blanked.sql
  - dbt_project/tests/assert_player_bio_withheld_listed.sql
  - dbt_project/tests/assert_withhold_rules_answer_key.sql
  - tests/test_withhold_wiring.py
  - .claude/task/262-player-bio-conflict-withheld/contract.md
  - .claude/task/262-player-bio-conflict-withheld/review.md
  - .claude/task/262-player-bio-conflict-withheld/review_input.patch

impact_map: >
  writers: base_apif__players is written by dbt only (no ingestion code, no raw table); it reads
  stg_apif__players, base_apif__fixture_events, base_apif__lineups, stg_apif__fixture_players and
  the seeds player_bio_corrections, country_name_overrides and player_id_overrides. No other model
  writes it. Its only direct reader is dim_player. No model reads the two flag columns that are
  renamed (grep over dbt_project/models, tests, macros, seeds, scripts, tests and site_v2/src finds
  them only in base.yml, base_apif__players.sql and assert_player_bio_conflicts_settled).
  downstream: `dbt ls --select base_apif__players+ --resource-type model`, run from the repo root
  with `--project-dir dbt_project` on this branch cut from gitlab/main:
  base_apif__players, dim_player, mart_competition_fixtures, mart_competition_research_list,
  mart_leaderboards, mart_match_days, mart_player_career, mart_player_competition_benchmarks,
  mart_player_fixture_stats, mart_player_index, mart_player_profile, mart_player_season_record,
  mart_roster, mart_team_competitions, mart_team_index, mart_team_momentum_window (16 models).
  Tests downstream of the model: 191 (`dbt ls --select base_apif__players+ --resource-type test`);
  the two that read it directly and change here are assert_player_bio_conflicts_settled and
  assert_identity_fields_never_blanked. dim_player takes the profile's birth date and nationality
  before the base value, so a withheld base value reaches a page only for a player with no profile.
  layer_rules: the withholding is cleaning and sits in base; check_layer_contract applies unchanged:
  no new model, no materialisation change, no per-competition file. Two macros are added, as the
  models already use macros for cleaning.
  deploy_order: one build; the nightly picks it up after merge. Renaming two columns of
  base_apif__players is safe because the only reader of them is the test that this change rewrites.
  blast_radius: measured read-only on prod before the build: 13 players have a conflicting birth
  date and 10 a conflicting nationality in base_apif__players, and every one has a row in
  player_bio_corrections (0 without), so no published value changes today. The MR states the same
  measure on its ci_mr tables.

approved_design:
  - none: no page output changes; a withheld birth date or nationality is blank, as the existing withheld values are

decisions_taken: >
  The smallest unit that is wrong is withheld: the value where it can be blanked. The test that
  caught a provider input stays at error severity and proves the value is withheld (#262, approved
  in chat, 15 Nov 2026). No test gets a where exemption, a lower severity or a filter that hides
  rows: the exemption added to assert_identity_fields_never_blanked is the set of players whose
  latest delivered values conflict, derived from stg_apif__players by the same macro as the
  settled test, so it does not read the flag it tests. The listing test is new and warn.

decisions_reserved: >
  none: how a withheld value looks on a page is the existing withheld-value form; no page, metric,
  name or rule is added.

done_when:
  - python scripts/ci_local.py --mr passes
  - dbt parse passes and sqlfluff lint passes on every changed model and macro
  - python -m pytest tests/test_withhold_wiring.py passes, and fails with the withheld_when_conflicting call removed from base_apif__players.sql
  - the MR pipeline is green, data:build:mr included

amendments: (none)
