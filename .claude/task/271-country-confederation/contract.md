# Task contract — a country's football confederation is stored, never inferred

objective: >
  Issue #271. Every country in `dim_country` carries its football confederation as stored data,
  or a note saying it belongs to none. Every team's region in `mart_team_index` is its country's
  stored confederation, and nothing infers it from the competitions a team plays.

refs: >
  #271. Plan and its three decisions approved in chat, 2026-11-09, through the coordinating
  session. #280 holds the three wrong-club ids found in the region diff.

scope_paths:
  - .claude/task/271-country-confederation/
  - dbt_project/seeds/countries.csv
  - dbt_project/seeds/team_country_corrections.csv
  - dbt_project/seeds/schema.yml
  - dbt_project/models/3_core/dim_country.sql
  - dbt_project/models/3_core/core.yml
  - dbt_project/models/5_marts/shared/mart_team_index.sql
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/docs/layering.md
  - tests/test_sentence_length_in_docs.py

impact_map: >
  writers: countries.csv is the only source of dim_country. mart_team_index is the only writer
  of a team's region_key and country_region_key. team_country_corrections feeds
  base_apif__teams_global, the only writer of dim_team.team_country.
  downstream: `dbt ls --select countries+ mart_team_index+ --resource-type model` (run 2026-11-09)
  gives: dim_country mart_team_index. team_country_corrections reaches base_apif__teams_global+:
  dim_team and every mart that carries a team's country (the lineage pasted in #269's contract).
  Consumption: scripts/export_site_data.py reads mart_team_index for teams_index.json
  (region_key, region_rank, country_region_key, country_order and the national team ranks).
  layer_rules: the mart reads core (dim_country, dim_team) and seeds. dim_country publishes a
  seed. dim_league stays the only reader of competition_registry. All are checked by
  check_layer_contract.py. No partition_by or cluster_by. No per-competition file.
  deploy_order: additive. One new column on dim_country (confederation). The mart_team_index
  column set is unchanged; its region values change. The merge rebuilds both in data:build:main.
  blast_radius: measured on prod, 2026-11-09. Shown teams whose region changes:
  - 6 Guadeloupe, 3 Martinique and 1 French Guiana clubs: UEFA to CONCACAF.
  - 3 Reunion clubs: UEFA to CAF.
  - 3 Tahiti and 2 New Caledonia clubs: UEFA to OFC.
  - Victoria United: CAF to CONCACAF. Warriors FC: CAF to AFC. Newmarket: UEFA to AFC. (#280)
  - The 61 Coupe de France clubs with no country get sourced countries. The overseas ones among
    them move with their territory, and a Mayotte club has no region.
  country_region_key and country_order follow the same stored values. The MR head lists every
  changed team.

decisions_taken: >
  The plan was approved in chat on 2026-11-09 through the coordinating session.
  countries.csv carries a confederation and a confederation_note. The note is filled only on a row
  with no confederation, and a test requires exactly one of the two.
  No confederation: Falkland Islands, Great Britain, Guernsey, Isle of Man, Jersey, Mayotte,
  Monaco, Northern Cyprus and Yugoslavia (dissolved).
  Associate members store their confederation: Reunion and Zanzibar CAF, Kiribati OFC.
  Non-FIFA full members store theirs: Bonaire, French Guiana, Guadeloupe, Martinique, Saint Martin
  and Sint Maarten CONCACAF; Tahiti and New Caledonia OFC.
  A team's region and its country's region both come from dim_country via team_country. The
  team_regions inference and the club and national-team country-region votes are removed.
  top_club_rank still ranks a club within its continental club competition (cup_region_key),
  because that ranks a competition, not a membership.
  Every shown team's country has a confederation. The only exemption is a country whose row
  records none with its note. A shown team with no country fails the test.
  The 61 shown Coupe de France clubs the provider sends no country for get one sourced row each in
  team_country_corrections.
  Fan-visible: the regions above change on the Teams hub. They apply #271's own rule, so the
  coordinating session decided them on 2026-11-09; the MR head lists every change.
  No new mechanism and no recurring cost.

decisions_reserved:
  - none: the three decisions were settled on 2026-11-09; a club whose country cannot be sourced goes to the coordinating session before any row is written.

done_when:
  - check_layer_contract.py, check_description_hygiene.py, sqlfluff on the changed models, dbt parse, and the offline Python suite all pass locally.
  - data:build:mr is green, including the new tests on dim_country, countries and mart_team_index.
  - Measured on the ci_mr datasets, every shown team's region equals its country's stored confederation. Russia is UEFA in dim_country. Every region change against prod is in the MR head.

amendments:
  - 2026-11-09: + dbt_project/docs/layering.md. Authority: the CPO's approval in this task's session, 2026-11-09. Content: strip the one sentence saying dim_country carries no confederation column; nothing else changes.
  - 2026-11-09: + tests/test_sentence_length_in_docs.py. Authority: the same approval. Content: layering.md's long-sentence pin moves from 43 to 42, because the stripped sentence was one of them.
