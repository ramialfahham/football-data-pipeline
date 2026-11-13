# Task contract — the two provider defects that failed the 13 Nov nightly, fixed at their source

objective: >
  Issue #262: the 13 Nov nightly failed two tests on provider data. (1) unique_dim_team_team_country:
  the provider's CONCACAF Nations League delivery of 13 Nov gives French Guiana's national team (team
  8118, "French Guyana") the country Guyana, which Guyana's own national team (5162) holds; through
  12 Nov it sent French-Guiana. One team_country_corrections row restores French Guiana.
  (2) assert_player_stat_corrections_within_limit: Copa del Rey 2026 reached 12.5% corrected player
  rows against the 8% limit, 18 of them Navalcarnero's in fixture 1644363 (Navalcarnero 2-3 Real
  Betis, 12 Nov 2026, after extra time), whose cards the cleaning blanks because the provider's card
  events name players with no stat line. The match's cards go into fixture_card_corrections from two
  match reports; the one carded player the provider holds no id for, Víctor Rodríguez, gets the
  warehouse's own player id. Each fix's data build fails on the other's test, so one MR carries both.

refs: >
  #262; routes ruled by the coordinating session on 2026-11-13 after the read-only trace of both
  failing rows: rfef.es is a stopped site, so the cards come from two independent match reports on
  sites whose robots and terms allow reading (the #176 source rules). The CPO answered in chat on
  2026-11-13 that every player has an id; the own-id plan was approved by the coordinating session
  the same day for the cto-reviewer route.

scope_paths:
  - dbt_project/seeds/team_country_corrections.csv
  - dbt_project/seeds/fixture_card_corrections.csv
  - dbt_project/seeds/player_id_overrides.csv
  - dbt_project/seeds/schema.yml
  - dbt_project/macros/player_id_override.sql
  - dbt_project/models/2_base/api_football/base_apif__fixture_players.sql
  - dbt_project/models/2_base/api_football/base_apif__lineups.sql
  - dbt_project/models/2_base/api_football/base_apif__players.sql
  - dbt_project/tests/assert_player_id_overrides_merged.sql
  - dbt_project/tests/assert_own_player_ids.sql
  - .claude/task/262-french-guiana-country/contract.md
  - .claude/task/262-french-guiana-country/review.md
  - .claude/task/262-french-guiana-country/review_input.patch

impact_map: >
  writers: dbt only; no ingestion, export or site change. The seeds team_country_corrections
  (base_apif__teams_global), fixture_card_corrections (base_apif__fixture_events,
  base_apif__fixture_players) and player_id_overrides (the player_id_override macro, used in 13
  places across 8 base models: base_apif__fixture_events, _fixture_players, _lineups, _players,
  _player_profiles, _player_team_season, _squads, _transfers).
  lineage: `dbt ls --resource-type model --output name --select base_apif__fixture_players+
  base_apif__lineups+ base_apif__players+ player_id_overrides+ fixture_card_corrections+` returns 89
  models: the 10 base models above with base_apif__fixture_players_from_lineups and
  base_apif__fixture_statistics; dim_player, dim_player_team_season_mapping, fct_fixture_event,
  fct_fixture_lineup, fct_fixture_player_stats, fct_fixture_team_stats, fct_transfer; 39
  int_player_*, int_team_*, int_legs__* and int_standings__official_rank models; and 33 marts, among
  them mart_player_fixture_stats, mart_player_profile, mart_player_index, mart_leaderboards,
  mart_roster, mart_competition_fixtures and mart_team_profile.
  ci_layer_rules: scripts/check_layer_contract.py, scripts/check_description_hygiene.py.
  deploy_order: one merge; the nightly rebuilds every model. No backfill.
  blast_radius: measured on prod 2026-11-13, read-only. The macro keeps every alias row's effect
  unchanged (it now reads alias rows only, as all 8 rows are). The assign_in_fixture row changes one
  stat line: fixture 1644363, Navalcarnero shirt 5, from the dropped placeholder 0 to player -1, so
  Navalcarnero gains one player-match row (120 minutes) and dim_player one player. The nine card rows
  replace the match's provider card events; the 18 Navalcarnero rows lose their cards_need_research
  blank, so Copa del Rey 2026 goes from 21 to 3 corrected rows of 168. Team 8118's country becomes
  French Guiana. The provider sends the placeholder 0 on 6,712 stat lines in 1,627 matches; none
  other changes, because an own id is only ever assigned by a researched row.

approved_design:
  - none: no page layout changes; team 8118 keeps its country, Navalcarnero's players in fixture 1644363 show their cards, and Víctor Rodríguez appears in that match as a player

decisions_taken: >
  Ruled by the coordinating session on 2026-11-13. (1) Team 8118 is French Guiana: the provider's own
  /teams delivery said French-Guiana until 12 Nov, and Concacaf's 2026/27 Nations League groups page
  lists French Guiana and Guyana as two separate national teams. The row records the wrong provider
  value, Guyana, so assert_team_country_corrections_still_needed warns when the provider returns to
  French-Guiana. (2) The cards of fixture 1644363 come from two match reports on allowed sites:
  laliga.com's Spanish match page (robots allows /partido/; its legal notice bans no automated
  reading) and 101tv.es's live report (robots allows it; no ban in its legal notice). They agree on
  every card: Navalcarnero, Varo López Y 54', Mario Jiménez Y 90+4', Víctor Rodríguez Y 116', Kensly
  Vázquez Y 120+2'; Real Betis, Lo Celso Y 37', Ruibal Y 90+4', Bartra Y 103', Ruibal second Y and red
  118'. Player ids are the provider's, from the match's stat lines; Varo López is 459051 (shirt 23).
  (3) Every player has an id (the CPO, in chat, 2026-11-13). The provider has none for Víctor
  Rodríguez: its stat line holds the placeholder 0, and Navalcarnero's squad list, /players, the
  profiles and Navalcarnero's other matches hold no record of him. The warehouse gives him its own
  id, -1. Own player ids are negative integers from -1 downwards, one per person, never reused:
  provider ids are positive and 0 is the provider's placeholder, so they can never collide; it is the
  convention of the five own team ids (-1 to -5). (4) The record reuses player_id_overrides with a
  new mode, assign_in_fixture, mirroring fixture_team_id_overrides' reattribute_in_fixture: the
  provider's placeholder 0 on team T's sheet or stat line with shirt N in fixture F becomes the own
  id. The seed gains fixture_id, team_id, shirt_number and source, blank on alias rows. The
  player_id_override macro reads alias rows only; a fixture-scoped macro next to it applies
  assign_in_fixture where base reads a sheet or a stat line (base_apif__fixture_players,
  base_apif__lineups, base_apif__players), before the placeholder is dropped. The player then has a
  stat line, a dim_player row and his card, like any other player. (5) assert_player_id_overrides_merged
  and the seed's unique test on the wrong id read alias rows only; assert_own_player_ids pins the own
  ids. This is a new kind of record, so the round includes cto-reviewer. No recurring cost.

decisions_reserved:
  - The provider's second id for Varo López (644022 on the events, 459051 on the stat line), a player_id_overrides alias question.

done_when:
  - dbt parse passes; sqlfluff lint passes on every changed model, macro and test.
  - The full pytest suite passes.
  - The MR's data build passes unique_dim_team_team_country, assert_player_stat_corrections_within_limit, assert_card_corrections_applied, assert_player_id_overrides_merged and assert_own_player_ids; compared with prod, team 8118's country, fixture 1644363's cards and player -1 are the only changes.

amendments:
  - 2026-11-13: + dbt_project/seeds/fixture_card_corrections.csv, dbt_project/seeds/player_id_overrides.csv, dbt_project/seeds/schema.yml, dbt_project/macros/player_id_override.sql, the three base models and the two tests — authority: the coordinating session's rulings of 2026-11-13 that one MR carries both seed fixes, because each fix's data build fails on the other's test, and that the own-player-id plan is built here; content: decisions (2) to (5).
