# Task contract — names arrive with their real characters, not HTML entities

objective: >
  Issue #268: the provider sends some names HTML-escaped (`&apos;`, `&amp;`, `&gt;`), and pages
  print the entity. Every name and place column is decoded where it first becomes a column, by one
  shared macro, and a test fails the build if an entity is left in any of them.

refs: >
  #268. Plan ruled by the coordinating session on 2026-11-09: widen to venue and place columns;
  decode the line-up player name in base_apif__lineups, where it first becomes a column; check
  only those first columns, not the marts.

scope_paths:
  - dbt_project/macros/decode_html_entities.sql
  - dbt_project/models/1_staging/api_football/stg_apif__coach_career.sql
  - dbt_project/models/1_staging/api_football/stg_apif__coaches.sql
  - dbt_project/models/1_staging/api_football/stg_apif__fixture_events.sql
  - dbt_project/models/1_staging/api_football/stg_apif__fixture_players.sql
  - dbt_project/models/1_staging/api_football/stg_apif__fixture_statistics.sql
  - dbt_project/models/1_staging/api_football/stg_apif__fixtures_next.sql
  - dbt_project/models/1_staging/api_football/stg_apif__leagues.sql
  - dbt_project/models/1_staging/api_football/stg_apif__lineups.sql
  - dbt_project/models/1_staging/api_football/stg_apif__player_profiles.sql
  - dbt_project/models/1_staging/api_football/stg_apif__player_teams.sql
  - dbt_project/models/1_staging/api_football/stg_apif__players.sql
  - dbt_project/models/1_staging/api_football/stg_apif__squads.sql
  - dbt_project/models/1_staging/api_football/stg_apif__standings.sql
  - dbt_project/models/1_staging/api_football/stg_apif__teams.sql
  - dbt_project/models/2_base/api_football/base_apif__lineups.sql
  - dbt_project/tests/assert_names_carry_no_html_entity.sql
  - dbt_project/tests/assert_html_entity_decode.sql
  - .claude/task/268-html-entity-names/contract.md
  - .claude/task/268-html-entity-names/review.md
  - .claude/task/268-html-entity-names/review_input.patch

impact_map: >
  writers: dbt only; no ingestion, seed or export change. The 14 staging models listed decode
  their name and place columns (player, first and last name, team, coach, league, venue name,
  venue city, venue address, birth place, birth country, country, nationality);
  base_apif__lineups decodes player_name where it parses it from the line-up JSON.
  lineage: `dbt ls --resource-type model --select <the 14 staging models>+` returns 117 of the
  project's 126 models, so every layer rebuilds; base_apif__lineups+ is inside that set.
  measured in prod staging on 2026-11-09 (read-only): only `&apos;`, `&amp;` and `&gt;` occur;
  players.player_name 361 distinct names, squads 131, player_profiles 120, fixture_players 25,
  line-up JSON about 22, venue_name 2, venue_city 27, venue_address 48; none in team, coach,
  league, country or nationality names.
  consumption: the export reads the same columns. A player URL is built from the name by
  `player_slug_with_id` in scripts/export_site_data.py, so an affected player's slug loses the
  `apos` piece (n-o-apos-reilly-<id> becomes n-o-reilly-<id>).
  ci_layer_rules: scripts/check_layer_contract.py, scripts/check_description_hygiene.py.
  deploy_order: one merge; the nightly rebuilds every model. No backfill.
  blast_radius: the affected names in mart_roster (353 distinct), mart_player_fixture_stats
  (234), mart_player_profile (233), mart_player_career (233), mart_leaderboards (132),
  mart_player_competition_benchmarks (67), mart_player_season_record (19, the line-up names) and
  mart_competition_fixtures.venue_name (2) show the real character; venue city and address in the
  team and player profiles likewise. Exact differences come from the MR build compared with prod.

approved_design:
  - none: no page output changes beyond names showing their real characters; no page file is touched

decisions_taken: >
  Ruled by the coordinating session on 2026-11-09 as a correctness fix. One macro,
  decode_html_entities, decodes in one pass the entities in its map (the five XML named entities
  and the two numeric apostrophes `&#39;`, `&#x27;`), so a double-escaped `&amp;apos;` decodes
  once, to `&apos;`; the map is data joined to the text's pieces, like translit_latin, which keeps
  the expression inside SQLFluff's parse-depth limit. It runs in staging on every name and place
  column, and in base_apif__lineups on the line-up player name, which staging keeps inside JSON
  where decoding `&quot;` would break the JSON. The guard test reads only those first columns; the
  marts copy them. Recurring cost: the guard test is a new nightly read of 414 MB (dry-run on
  prod, 2026-11-09), about 12.4 GB and $0.08 a month, approved by the CPO in chat, 2026-11-09.
  No new mechanism.

decisions_reserved:
  - Any entity outside the macro's map fails the guard test and is added to the map in a later task.

done_when:
  - dbt parse succeeds from the repo root.
  - python -m pytest tests -q is green, and the offline gates pass.
  - SQLFluff adds no violation on any changed model or test.
  - CI's data:build:mr is green, both new tests included.
  - Every changed model and everything downstream is compared with prod both ways, and every difference is listed.
  - The guard test's nightly bytes are measured.
  - The MR head lists before and after for a sample of the changed names.

amendments: (none)
