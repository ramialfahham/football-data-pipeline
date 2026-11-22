# Task contract — crests and league logos served from our own domain (MR A: the data side)

objective: >
  The nightly ingest stores each team crest and league logo in a private Cloud Storage bucket,
  shrunk to 48 px and 104 px as WebP, and records each object in a raw state table. `dim_team` and
  `dim_league` carry the site path `/crests/{teams|leagues}/{id}-104.webp` only where an object
  exists, else null, so no served column names the provider's host. The site build copies the bucket
  into `site_v2/public/crests/`, Firebase serves it from our domain with a 7-day cache, and the
  built-pages check fails a full export whose crest paths are not files in `dist/`. The bucket and
  the first fill follow the merge; no provider call or bucket write is made before the CPO runs the
  two `gcloud` commands in the runbook.
refs: "#36, #290 (gate item: crests from our own host)"

scope_paths:
  - ingestion/api_football/loads/crests.py
  - ingestion/api_football/orchestrator.py
  - ingestion/api_football/settings.py
  - ingestion/api_football/requirements.txt
  - requirements.txt
  - scripts/sync_crests.py
  - scripts/nightly_site_deploy.py
  - site_v2/firebase.json
  - site_v2/.gitignore
  - site_v2/scripts/check-built-pages.mjs
  - site_v2/scripts/check-built-pages.test.mjs
  - dbt_project/models/1_staging/api_football/sources.yml
  - dbt_project/models/1_staging/api_football/stg_apif__crest_objects.sql
  - dbt_project/models/1_staging/api_football/stg_apif__generic.yml
  - dbt_project/models/2_base/api_football/base_apif__crest_objects.sql
  - dbt_project/models/2_base/api_football/base.yml
  - dbt_project/models/3_core/dim_team.sql
  - dbt_project/models/3_core/dim_league.sql
  - dbt_project/models/3_core/core.yml
  - dbt_project/models/docs/shared_columns.md
  - dbt_project/models/5_marts/domestic_league/domestic_league.yml
  - dbt_project/models/5_marts/shared/shared.yml
  - dbt_project/tests/assert_served_crest_path_has_an_ok_object.sql
  - docs/data_contract.md
  - deploy/nightly/README.md
  - tests/test_crests.py
  - tests/test_sync_crests.py
  - tests/test_nightly_site_deploy.py
  - .claude/task/36-crest-hosting/contract.md
  - .claude/task/36-crest-hosting/review.md
  - .claude/task/36-crest-hosting/review_input.patch

impact_map: >
  writers: RAW_APIF_CREST_OBJECTS is new and has one writer, `ingestion/api_football/loads/crests.py`
  (one payload row per run through `load_json_to_bq`, append, payload-only raw table). The bucket
  objects have one writer, the same module. `dim_team` and `dim_league` stay the only models that
  publish a crest address. Nothing else writes `team_logo_url` or `league_logo_url`.
  downstream: `dbt ls --select "dim_team+ dim_league+"` run on this branch's base (d1de075f) lists
  dim_competition_season, dim_league, dim_player_team_season_mapping, dim_team, fct_fixture,
  fct_fixture_team_stats, fct_standings, 18 int_ models (competition_season, knockout_ties,
  legs, player, standings, team) and the marts mart_competition_fixtures, mart_competition_index,
  mart_competition_research_list, mart_competition_season_summary, mart_fixture_standing_context,
  mart_head_to_head, mart_leaderboards, mart_match_days, mart_matchday_insights, mart_next_matchday,
  mart_player_career, mart_player_competition_benchmarks, mart_player_fixture_stats,
  mart_player_index, mart_player_momentum, mart_player_profile, mart_player_season_record,
  mart_player_squad_benchmarks, mart_player_window_metrics, mart_roster, mart_standings,
  mart_team_competition_benchmarks, mart_team_competitions, mart_team_fixtures, mart_team_index,
  mart_team_leaderboards, mart_team_market_value, mart_team_momentum_window,
  mart_team_page_window_metrics, mart_team_profile, mart_team_season, mart_team_season_insights,
  mart_team_season_record and mart_team_window_metrics. Only `team_logo_url` and `league_logo_url`
  (and their renamed forms in the marts) change value. Only `dim_team` and `dim_league` read the
  base models that carry the provider address (grep over `3_core`, `4_intermediate`, `5_marts`).
  The export script reads the marts' logo columns into the `crest` and `logo_url` payload keys and
  needs no edit.
  layer_rules: `check_layer_contract.py` (staging = raw cleanup; base = first logic; core reads
  base): the new staging model reads only the raw source; the new base model reads only that staging
  model; the dims read the base model. A raw table written is declared in `sources.yml`.
  `check_description_hygiene.py` bounds every description to 1,024 characters.
  deploy_order: (0) the CPO creates the empty state table; (1) merge; (2) the CPO creates the bucket and grants the service account; (3) the
  next `fdp-nightly` runs the pre-flight and the first fill, then `dbt build` publishes the paths;
  (4) the next `fdp-site` run copies the bucket into `dist/` before `npm run build`. Before (2) the
  phase finds no bucket, logs it and writes nothing, the state table stays empty, the dims publish
  null and the pages show initials. The state table must exist before the merge, because the MR data
  build, the main build and the nightly's `dbt build` read it as a source: step (0), before the merge,
  is the CPO creating the empty table with the ingest's own helper (`ensure_raw_table_partitioned`,
  the command in the runbook; no rows, no provider call). The crest phase creates the same table on
  its first run. After (3) and before (4) there is no site build that
  reads the paths, so no page can 404; the first `fdp-site` run after this merge already carries
  the sync step and the check rule.
  blast_radius: every page that shows a crest or a league logo: the address changes from the
  provider's to our path, only where an object exists. The committed sample still holds provider
  addresses until the next MR regenerates it, so the built-pages pin stays at its current count.
  Cost: Firebase Hosting transfer (measured after the first fill); a nightly BigQuery read of the
  latest raw teams and leagues rows, whose dry run on prod reports 261 MB and 5.4 MB (about 8 GB a
  month, a few cents); and about 475 image requests a night after the first fill. The discovery
  query run read-only on prod returns 3,279 team ids and 48 league ids, every address in the
  provider's `/football/{teams|leagues}/{id}.png` shape, which is 3,327 images and 6,654 files.
  The no-provider-host guarantee on the published columns is two `expression_is_true` tests on
  `dim_team.team_logo_url` and `dim_league.league_logo_url`, and a Python test that no model in
  `3_core`, `4_intermediate` or `5_marts` outside the two dimensions and one mapping reads a base or
  staging team or league model.

depends_on:
  - none: the merged check (!507) and crest-fill MR are on main; no open MR's code is needed
shared_files:
  - none: no design baseline, chart manifest or chart pin changes

decisions_taken: >
  The CPO's ruling on how crests and placeholders look (approved in chat, 2026-11-22, #36, the
  comment on #36) adds: each crest stored shrunk to 48 px and 104 px as WebP with Pillow as a pinned
  direct dependency, and `/crests/**` served with a 7-day cache. The coordinating session's messages
  of 2026-11-22 accept plan revision 2 (private bucket, the site build copying it into `dist/`, the
  path `/crests/{teams|leagues}/{id}-104.webp` in `dim_team` and `dim_league`, the pre-flight that
  measures whether image requests count against the daily quota) and order MR A built whole. The
  merge is the approval of the mechanism, the permanent path and the provider downloads; the MR
  head lists them with the dependency at the top. `google-cloud-storage` 2.19.0 is already installed
  through `dbt-bigquery` and becomes a direct pin. No provider call and no bucket write is made from
  the builder's machine.

decisions_reserved:
  - "the permanent path `/crests/{teams|leagues}/{id}-104.webp` and the bucket name `football-data-pipeline-gcp-crests`: public identifiers, listed in the MR head for the CPO's merge"
  - "the new mechanism (private bucket, raw state table, a crest phase in `fdp-nightly`, `scripts/sync_crests.py` in the site build) and the provider image downloads (the first fill, then about 475 a night): listed in the MR head for the CPO's merge"
  - "the Pillow dependency: pinned and listed in the MR head for the CPO's merge"

approved_design:
  - none: no page output changes in this MR; the next MR regenerates the committed sample and lowers the pin

done_when:
  - "`python -m pytest tests/test_crests.py tests/test_sync_crests.py tests/test_nightly_site_deploy.py tests/test_nightly_entrypoint_parity.py -q` passes."
  - "`cd site_v2 && node --test` passes."
  - "`.venv/Scripts/dbt.exe parse --project-dir dbt_project` passes, and `python scripts/check_layer_contract.py`, `python scripts/check_description_hygiene.py` and `python scripts/check_relationships_coverage.py` pass."
  - "`python scripts/ci_local.py --mr` passes."

amendments: (none)
