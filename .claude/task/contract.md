# Task contract — repair garbled player names and stop them shipping

objective: >
  Issue #248: the provider sends some player names as UTF-8 read as Latin-1 or Windows-1252. Base
  repairs them so every name downstream is correct, and a check fails the build when exported data
  holds wrongly decoded text.

refs: >
  #248, plan approved in chat 2026-11-06. Found by #243.

scope_paths:
  - dbt_project/macros/repair_garbled_text.sql
  - dbt_project/models/2_base/api_football/base_apif__players.sql
  - dbt_project/models/2_base/api_football/base_apif__player_profiles.sql
  - dbt_project/models/2_base/api_football/base_apif__fixture_events.sql
  - dbt_project/tests/assert_garbled_text_repair.sql
  - dbt_project/models/3_core/core.yml
  - dbt_project/models/docs/shared_columns.md
  - site_v2/scripts/check-exported-text.mjs
  - site_v2/scripts/check-exported-text.test.mjs
  - site_v2/scripts/build-wiring.test.mjs
  - site_v2/package.json
  - site_v2/src/data/fixtures/1528965.json
  - site_v2/src/data/fixtures/1553193.json
  - site_v2/src/data/fixtures/1635716.json
  - site_v2/src/data/fixtures/1638563.json
  - site_v2/src/data/teams/165.json
  - site_v2/src/data/teams/169.json
  - site_v2/src/data/teams/172.json
  - site_v2/src/data/teams/173.json
  - site_v2/src/data/teams/182.json
  - site_v2/src/data/teams/192.json
  - site_v2/src/data/teams/211.json
  - site_v2/src/data/teams/867.json
  - tests/fixtures/font_coverage/baseline.json
  - tests/fixtures/design_inventory/baseline.json
  - tests/fixtures/design_inventory/baseline_quick.json
  - .claude/task/contract.md
  - .claude/task/review.md
  - .claude/task/review_input.patch
  - .claude/task/acceptance_evidence.md
  - .claude/task/rendered_page_evidence.md

impact_map: >
  writers: dbt only; no ingestion change, raw stays as received. The garbling comes from the
  provider: one string holds a broken and a correct letter together, which no wrong decode on our
  side produces.
  lineage: `dbt ls --resource-type model --select base_apif__players+1 base_apif__player_profiles+1
  base_apif__fixture_events+1` returns base_apif__fixture_events, base_apif__fixture_players,
  base_apif__fixture_statistics, base_apif__lineups, base_apif__player_profiles, base_apif__players,
  dim_player, fct_fixture_event; the full `+` selection is 84 models. No model joins or tests on a
  name: `grep -rn "player_name" dbt_project/tests` is empty, and base_apif__fixture_players,
  base_apif__fixture_statistics and base_apif__lineups read event ids, types and the assist's
  presence, never the name's text. The repair keeps a null a null, so assisted_goal_events holds.
  consumption: dim_player feeds every player name the export reads, and
  mart_competition_fixtures falls back to fct_fixture_event's names. The export builds player slugs
  from the name, so the slug of each repaired name changes with its name.
  ci_layer_rules: scripts/check_layer_contract.py, scripts/check_description_hygiene.py.
  deploy_order: one merge; the nightly dbt build rebuilds. No backfill, no raw write.
  blast_radius: measured on prod: 415 players in dim_player, 38 distinct event names, and the two
  nationalities Côte d'Ivoire and Türkiye change their text; no number changes. The other text
  columns of dim_player, dim_coach, dim_team, fct_fixture, fct_fixture_event, dim_league and
  dim_country hold no garbled value. Offline run of the rule on all 494 flagged values: 493
  repaired, 0 failures, and the 494th, a correct name, left alone.

approved_design:
  - match: #132
  - team: #134

decisions_taken: >
  The plan on #248, approved in chat 2026-11-06. New mechanisms, both declared there: the dbt macro
  repair_garbled_text, and check-exported-text.mjs in the site's prebuild. No recurring cost: the
  macro runs inside three existing base builds. The rule covers Latin letters only, and its accepted
  limit is stated on the plan: garbled Cyrillic passes unrepaired, and the check catches it only when
  it holds a control character, so that German text such as a sharp s before a closing quote never
  fails the build. Nationality is repaired with the names, because it carries the same defect.
  Player URLs of repaired names change at the next deploy; the site is unlisted and noindex. The
  page designs do not change, only the letters of the names in the data.

decisions_reserved:
  - Player 275169's provider name carrying a leading "0" and spaces is another defect, reported to the CPO after this MR.

acceptance_criteria:
  - Every player name on the site shows its own letters: "A. Maksimović", "M. Ljubičić", "K. Urbański", "J. Potočnik", "A. Voitinovičius", "L. Jovanović", "M. Cvetković", "N. Kovač".
  - A check fails the build when exported data holds text decoded in the wrong character set.

done_when:
  - dbt_project/tests/assert_garbled_text_repair.sql passes in data:build:mr.
  - check-exported-text.mjs passes on the committed sample and its node tests prove a garbled value fails.
  - npm run build in site_v2 passes; the whole pytest tests passes; SQLFluff passes on the changed models.
  - The prod comparison of the three base models shows every changed row is a repair.

amendments:
  - 2026-11-06: + dbt_project/models/3_core/core.yml, dbt_project/models/docs/shared_columns.md — authority: the plan on #248, approved in chat 2026-11-06; content: the column descriptions state the repair that plan approved.
