# Task contract — a team's table is the section of its current phase

objective: >
  Issue #277 follow-up: a team's shown rank and form come from the standings section of the phase
  it is playing, by one rule that the Team page's standing and the team-season marts share. A
  cross-group ranking is recognised by its structure as well as its name, and is never a team's
  table. The team index orders two clubs with the same name the same way on every build.

refs: >
  #277; the follow-up ruled by the coordinating session on 2026-11-09 after the prod comparison of
  !411 showed 46 team-seasons (APD 2026, BPL 2024–25, KL1 2026, VL 2026) on an earlier or overall
  table. The lineup duplicate found by the same comparison is #281, not this task.

scope_paths:
  - dbt_project/models/4_intermediate/shared/int_standings__section_kinds.sql
  - dbt_project/models/4_intermediate/shared/int_standings__section_kinds.yml
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season__standings_primary.sql
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season__table_state.sql
  - dbt_project/models/4_intermediate/domestic_league/team_season/int_team_season.yml
  - dbt_project/models/5_marts/shared/mart_standings.sql
  - dbt_project/models/5_marts/shared/mart_team_competitions.sql
  - dbt_project/models/5_marts/shared/mart_team_index.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/tests/assert_standings_cross_group_rankings.sql
  - dbt_project/tests/assert_team_standing_section_cases.sql
  - dbt_project/tests/assert_every_standings_section_has_a_table_kind.sql
  - dbt_project/tests/assert_team_season_games_not_short_of_standings.sql
  - tests/test_sentence_length_in_docs.py
  - tests/test_no_decision_history_in_code.py
  - .claude/task/277-standings-section/contract.md
  - .claude/task/277-standings-section/review.md
  - .claude/task/277-standings-section/review_input.patch

impact_map: >
  writers: dbt only; no ingestion, seed or export change. int_standings__section_kinds moves from
  grain (group_name) to (league_code, season_api_year, group_name); its readers mart_standings and
  int_team_season__table_state join on the three keys, and int_team_season__standings_primary
  becomes its third reader. int_team_season__standings_primary gains group_name;
  mart_team_competitions takes its standing section from it.
  lineage: `dbt ls --resource-type model --select int_standings__section_kinds+
  int_team_season__standings_primary+ mart_team_competitions+ mart_team_index+` returns 19
  models: int_standings__official_rank int_standings__section_kinds int_team_profile__yoy
  int_team_season__deserved_vs_actual int_team_season__standings_primary
  int_team_season__table_by_time int_team_season__table_state mart_competition_fixtures
  mart_competition_index mart_fixture_standing_context mart_match_days mart_matchday_insights
  mart_next_matchday mart_standings mart_team_competitions mart_team_index mart_team_profile
  mart_team_season mart_team_season_insights.
  consumption: the export reads the same columns; mart_standings' table_kind for two sections
  changes to ranking, so the WC 2026 and ACN 2027 competition pages drop those two cross-group
  ranking tables as they drop every other one.
  ci_layer_rules: scripts/check_layer_contract.py, scripts/check_description_hygiene.py.
  deploy_order: one merge; the nightly rebuilds every model. No backfill.
  blast_radius: measured on the !411 build: the rule corrects 46 team-seasons and changes the
  standing of the 4 WC 2026 third-placed teams back to their group; the structural ranking rule
  reclassifies 2 sections (WC 2026 "Group Stage", ACN 2027 "Groups"); 2 clubs in the team index.
  Exact differences come from the MR build compared with prod.

approved_design:
  - none: the page change is the existing rule that a cross-group ranking is never shown, applied to two sections

decisions_taken: >
  Ruled by the coordinating session on 2026-11-09 as correctness fixes. A team's table is the
  section named in its latest played round, otherwise the section in which it has played most; a
  ranking is never a team's table; the provider's section order decides what is still tied. A round
  names a section when the section's name is in the round's name, or the round's stage (its name
  before the " - " number) is in the section's name. The rule lives once, in
  int_team_season__standings_primary, and mart_team_competitions reads it. A section is a ranking
  when its name matches a ranking pattern of standings_table_kinds, or when every team in it sits in
  exactly one other non-ranking section of the league-season and no two of its teams in the same
  one. The team index order ends with team_sk. No new mechanism, no recurring cost.

decisions_reserved:
  - The lineup duplicate (#281).

acceptance_criteria:
  - A team in a split season shows its rank and form in the phase it is playing (APD 2026 Clausura, BPL 2024 Charleroi in its Qualifying Round, KL1 2026, VL 2026 Ilves).
  - A team in a group tournament shows its own group's rank, never a cross-group ranking (EURO 2024 Netherlands).
  - The Team page's standing and the team-season marts take a team's table from one rule.
  - WC 2026 "Group Stage" and ACN 2027 "Groups" are rankings, and every real group stays a group.
  - No section of a split-season league (BPL, VL, KL1, LMX, APD) is ever classified as a ranking.
  - Two clubs with the same name in one country keep the same order on every build.

done_when:
  - dbt parse succeeds from the repo root.
  - python -m pytest tests -q is green, and the offline gates pass.
  - SQLFluff adds no violation on any changed model.
  - CI's data:build:mr is green; every changed model and everything downstream is compared with prod both ways, and every difference is listed.
  - The before/after list of shown rank and form is posted on #277.

amendments:
  - 2026-11-09: + dbt_project/tests/assert_every_standings_section_has_a_table_kind.sql, dbt_project/tests/assert_team_season_games_not_short_of_standings.sql — authority: decisions_taken (the structural ranking rule; tests updated with the change); content: the kind test recomputes the structural rule as well as the name patterns, and the second test's comments name what int_team_season__standings_primary now reads.
