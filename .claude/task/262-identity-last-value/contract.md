# Task contract — identity fields take their last non-NULL value; tests check them against our data

objective: >
  Issue #262, second part: a team's and a player's identity fields never go blank because the
  latest delivery left them empty. Base takes each identity field's last non-NULL value across the
  stored deliveries, and four warning tests show where the chosen values disagree with the rest of
  our data, each with a named case.

refs: >
  #262 (the CPO's principle note of 2026-11-11). The design (last non-NULL in base, then consistency
  tests) and the scope limit (only the three base models that pick identity fields, their base.yml
  entries and the tests; identity fields only; no ingestion, raw or staging change) were set by the
  CPO and relayed by the coordinating session on 2026-11-12. The nightly fix is !427.

scope_paths:
  - dbt_project/models/2_base/api_football/base_apif__players.sql
  - dbt_project/models/2_base/api_football/base_apif__player_profiles.sql
  - dbt_project/models/2_base/api_football/base_apif__teams_global.sql
  - dbt_project/models/2_base/api_football/base.yml
  - dbt_project/tests/assert_player_nationality_matches_national_team.sql
  - dbt_project/tests/assert_club_country_matches_domestic_league.sql
  - dbt_project/tests/assert_player_birth_date_plausible.sql
  - dbt_project/tests/assert_identity_names_stable.sql
  - dbt_project/tests/assert_identity_fields_never_blanked.sql
  - .claude/task/262-identity-last-value/contract.md
  - .claude/task/262-identity-last-value/review.md
  - .claude/task/262-identity-last-value/review_input.patch

impact_map: >
  writers: dbt only; no ingestion, raw, staging, seed or export change. base_apif__players and
  base_apif__player_profiles feed dim_player; base_apif__teams_global feeds dim_team.
  lineage: `dbt ls --resource-type model --output name --select base_apif__players+
  base_apif__player_profiles+ base_apif__teams_global+` returns 29 models: base_apif__player_profiles
  base_apif__players base_apif__teams_global dim_player dim_player_team_season_mapping dim_team
  mart_competition_fixtures mart_fixture_standing_context mart_leaderboards mart_match_days
  mart_matchday_insights mart_player_career mart_player_competition_benchmarks
  mart_player_fixture_stats mart_player_index mart_player_profile mart_player_season_record
  mart_roster mart_standings mart_team_competition_benchmarks mart_team_competitions
  mart_team_fixtures mart_team_index mart_team_leaderboards mart_team_market_value
  mart_team_momentum_window mart_team_profile mart_team_season mart_team_season_insights.
  consumption: the export reads the same columns; no column is added or removed.
  ci_layer_rules: scripts/check_layer_contract.py, scripts/check_description_hygiene.py.
  deploy_order: one merge; the nightly rebuilds every model. No backfill.
  blast_radius: measured on prod 2026-11-12, read-only, by running the compiled models against prod
  and comparing with the prod tables. base_apif__players, 156,203 rows: 36 birth dates, 37
  nationalities, 38 first names, 40 last names and 8 names change (the empty-field fills, and names
  where rows of one delivery disagree); photo and both conflict flags unchanged. base_apif__player_
  profiles, 51,696 rows: 2 names change (tie order inside one delivery), nothing else. base_apif__
  teams_global, 3,417 rows: nothing changes today, slugs included. Re-measured on 2026-11-13 after
  base_apif__player_profiles treats a placeholder birth date as empty before the pick: 51,700 rows,
  still 2 names and nothing else. The four warning tests list 771, 5, 22 and 138 rows on today's
  data, and every named case holds. assert_identity_fields_never_blanked returns 0 rows on the new
  logic and 37 nationalities, 36 birth dates and its named case on prod's current tables. Bytes:
  base adds none (same tables, same columns); the five tests scan about 0.42 GB a night against a
  ~85 GB green nightly.

approved_design:
  - none: no page layout changes; 38 players show a birth date, nationality or name that an earlier delivery gave

decisions_taken: >
  Set by the CPO on 2026-11-12, relayed by the coordinating session. (1) Identity fields only:
  player name, first name, last name, birth date and nationality; team name and country. Every other
  field (photo, height, weight, position, birth place, venue, code, founded year) keeps today's
  latest-row rule. (2) Each identity field takes its last non-NULL value, in the order base already
  uses to pick a row (source priority, then the latest delivery, then the existing tie order); no
  field takes its first non-NULL value, because a later delivery is how the provider corrects
  itself. (3) A player's conflict flags describe the delivery the value came from. (4) A team's URL
  slug keeps reading the settled row's provider country, so a country filled from another row moves
  no URL; the slug follows the name, as it does today. (5) The four tests are warnings that list
  mismatches: nationality against the national teams a player appeared for; a club's country
  against its domestic league's; a birth date that makes a player younger than 15 or older than 45
  in a match he played; a player's surname that differs between /players deliveries (compared
  without accents) and a team's name that differs between competitions. Each has a named case. No new mechanism, no recurring cost
  beyond the measured test scans. (6) assert_identity_fields_never_blanked is error severity: the
  coordinating session's test-design ruling of 2026-11-13, implementing the CPO's design of
  2026-11-12. It pins decision (2) and adds no rule: a player's birth date or nationality, or a
  team's country, is never blank in base while a delivery holds one, unless player_bio_corrections
  left it blank; named case H. Abe (33085). (7) A /players nationality that is blank or whitespace
  counts as empty before the pick, so it can never be chosen over a real one.

decisions_reserved:
  - What to do with each listed mismatch (seed corrections go through the #262 research route).
  - Horoya and Hafia in CAFCL 2025/26 (fixture_team_id_overrides, after research), a separate change.

done_when:
  - dbt parse passes; sqlfluff lint passes on every changed model and test.
  - The full pytest suite passes.
  - The MR's data build passes, and its tables compared with prod show the measured identity changes and no other.

amendments:
  - 2026-11-12: + dbt_project/tests/assert_identity_fields_never_blanked.sql — authority: decision (6) of decisions_taken, the coordinating session's test-design ruling of 2026-11-13; content: an error-severity test that fails where a player's birth date or nationality, or a team's country, is blank in base while a delivery holds one, with a named case. In the same round base_apif__player_profiles treats a placeholder birth date as empty before the pick, as base_apif__players already does, and base_apif__teams_global computes "has provider attributes" once.
