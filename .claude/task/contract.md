# Task contract — fix the leagues country/flag JSON path

objective: >
  `dim_league.league_country` and `country_flag_url` are NULL on all 45 rows because
  `stg_apif__leagues.sql` reads `$.league.country` and `$.league.flag`, paths that do not exist
  in the API-Football `/leagues` payload. The provider returns `country` as a SIBLING of
  `league` (`$.country.{name,code,flag}`). Repoint the two extractions and add the `not_null`
  test whose absence let this ship silently. This unblocks #62 step 3 (`mart_competition_index`),
  whose region column had no source for its single-country branch.
refs: GitLab #62 (step 3 blocker, 2026-08-14 note), #69 (countries entity), #54 (page design)

scope_paths:
  - dbt_project/models/1_staging/api_football/stg_apif__leagues.sql
  - dbt_project/models/3_core/core.yml
  - .claude/active_work.md

impact_map: >
  writers: ONE. `ingestion/api_football/loads/catalog.py:38` writes `RAW_APIF_LEAGUES`
    (WRITE_APPEND) with the whole `/leagues` response as a JSON `payload` column. It is the
    only `raw_table("LEAGUES")` call in the repo (`grep -rn "LEAGUES" ingestion/ --include=*.py`
    → `ingest_plan.py:134`, `loads/catalog.py:1,38`). The loader is NOT changed — it already
    stores the field; only the extraction path in staging is wrong.

  downstream: `dbt ls --select stg_apif__leagues+ --resource-type model` (dbt 1.7.19,
    .venv/Scripts/dbt.exe, run 2026-08-15) → 17 models:
      1_staging.api_football.stg_apif__leagues
      2_base.api_football.base_apif__leagues
      2_base.api_football.base_apif__league_entity
      2_base.api_football.base_apif__competition_seasons
      3_core.dim_league
      3_core.dim_competition_season
      3_core.dim_player_team_season_mapping
      3_core.fct_standings
      4_intermediate.domestic_league.team_season.int_team_season__deserved_vs_actual
      4_intermediate.domestic_league.team_season.int_team_season__standings_primary
      5_marts.shared.mart_fixture_standing_context
      5_marts.shared.mart_roster
      5_marts.shared.mart_standings
      5_marts.shared.mart_team_profile
      5_marts.shared.mart_team_season
      5_marts.domestic_league.mart_matchday_insights
      5_marts.domestic_league.mart_team_season_insights

  blast_radius: NO mart number changes. The two columns are read by NOTHING downstream of
    `dim_league`: `grep -rn "league_country\|country_flag_url" dbt_project/models/4_intermediate/
    dbt_project/models/5_marts/` → zero hits; the same grep over `base_apif__competition_seasons`
    and `dim_competition_season` → zero hits. The full-repo grep finds them only in
    `stg_apif__leagues.sql`, `base_apif__leagues.sql`, `dim_league.sql`, `core.yml` and a comment
    in `scripts/sync_dbt_vars.py:45`. The 15 other downstream models are reached through the
    season/coverage columns, which this change does not touch.
    This is a VALUE change, not a SCHEMA change — both columns already exist with the same
    names and types, so no `select *` consumer gains or loses a column. Measured effect on
    `dim_league` (45 rows): `league_country` 0 → 45 non-null, `country_flag_url` 0 → 21 non-null.
    The 24 rows that stay NULL on flag are the international competitions, which the provider
    returns as `{"name":"World","code":null,"flag":null}` — hence `not_null` on `league_country`
    only, never on `country_flag_url`.

  layer_rules: `scripts/check_layer_contract.py` — staging stays raw cleanup only (this is a JSON
    path correction, no logic added), and staging/base materialisation is a LAYER setting in
    `dbt_project.yml`; no per-model override is introduced. No per-competition file is added, so
    the no-new-model rule is untouched. `league_code` handling is unchanged.

  deploy_order: no migration ordering problem. Staging and base are TABLES, so the corrected
    values appear only after the models rebuild; until then `dim_league` keeps today's NULLs,
    which is what every consumer already tolerates (nothing reads the columns). A dbt model path
    is inside `.data_paths_prod`, so merging triggers `data:build:main` and prod picks the fix up
    on that run — no manual step, and no dependency on the 04:00 nightly, which has no schedule.
    The new `not_null` test runs in the same build; it can only go red if the provider stops
    returning `$.country.name`, which is the signal it exists to give.

decisions_taken: >
  CPO go, 2026-08-15, in this conversation: "fix the staging path, own MR" — given after the
  measured lookup below was presented with three named alternatives (fix the extraction, project
  the registry's `country`, or wait for #69's countries seed).

  EVIDENCE the fix rests on (priced with `bq query --dry_run` first, 2,325,889 bytes, whole
  population not a sample — latest payload per `league_code`, 45 rows):
    $.league.country  0/45   <- what staging reads today
    $.league.flag     0/45   <- what staging reads today
    $.league.logo    45/45   <- same object, correct path, which is why logos work
    $.country.name   45/45
    $.country.code   21/45
    $.country.flag   21/45
  Sample payload: `$.league` = {"id":32,"logo":"...","name":"World Cup - Qualification Europe",
  "type":"Cup"}; `$.country` = {"code":null,"flag":null,"name":"World"}.

  The defect is ISOLATED, not systemic (`bq` 460,819 bytes): the other three country columns read
  correct paths and are populated — `dim_team.team_country` 3,241/3,271,
  `dim_coach.coach_birth_country` 6,400/8,368, `dim_player.player_birth_country` 39,035/135,269.
  So this MR does not touch them; #69 still owns reconciling their values.

  This does NOT reverse the CPO's ruling 3 of 2026-08-14 (`escalations.log`), that the registry's
  hand-typed `country` stays out of the seed and countries become their own entity under #69. That
  ruling reasoned the registry copy would be a third copy of provider-sourced data; confirming a
  real provider source strengthens it. `sync_dbt_vars.py:45`'s comment becomes accurate once this
  merges, so it is deliberately NOT edited.

  NEW MECHANISM: none. A `not_null` test is the existing dbt test convention already used on five
  columns of this same model in this same file.
  RECURRING COST: none material. No new model, no new table, no extra scheduled run. The added
  test scans `dim_league`, 45 rows.

decisions_reserved:
  - Which string the competitions page renders for the 21 single-country competitions. The
    provider's names are not display-ready — `Saudi-Arabia`, `South-Korea`, `USA` — and the other
    24 read `World`. Names are copy and copy is the CPO's (§10). This MR lands the SOURCE only;
    it does not decide the rendered text, and #62 step 3 must not assume it.
  - Whether `mart_competition_index` reads `dim_league.league_country` directly at step 3 or waits
    for #69's `dim_country` to supply canonical names. Reserved to the CPO; not decided here.

done_when:
  - `stg_apif__leagues.sql` extracts `$.country.name` and `$.country.flag`; no other line changes.
  - `dbt parse` succeeds against the .venv dbt (1.7.19).
  - `python -m sqlfluff lint dbt_project/models/1_staging/api_football/stg_apif__leagues.sql
    --templater jinja --dialect bigquery` from the repo root is clean, full rule set.
  - The compiled SELECT, run against RAW in BigQuery and priced first, returns 45/45 non-null
    `country` and 21/45 non-null `country_flag_url`.
  - The `not_null` test is shown RED against the CURRENT (broken) extraction before being
    accepted — a test that cannot fail is decoration.
  - `python .claude/hooks/git_discipline.py --review-patch` builds the patch; the review cycle
    runs with `analytics-engineer-reviewer` (routed by `dbt_project/**`) and `scope-auditor`.

amendments: (none)
