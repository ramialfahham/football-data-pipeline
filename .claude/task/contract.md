# Task contract — standardize country names in base

objective: >
  `!43` gave `dim_league.league_country` a real provider source, but the provider's strings are not
  display-ready: it hyphenates multi-word country names (`Saudi-Arabia`, `South-Korea`) and
  abbreviates one (`USA`). Per the CPO ruling of 2026-08-14 ("Our transformation layer is the place
  where we clean, reconcile and standardize the data"), restated 2026-08-15 as "we standardize in
  base", correct these in the base layer so `dim_league` publishes a finished name. This removes
  the last thing standing between #62 step 3 and `mart_competition_index`.
refs: GitLab #62 (step 3), #69 (countries entity, supersedes this later), #54 (page design)

scope_paths:
  - dbt_project/seeds/country_name_overrides.csv
  - dbt_project/seeds/schema.yml
  - dbt_project/models/2_base/api_football/base_apif__leagues.sql
  - dbt_project/models/2_base/api_football/base.yml
  - dbt_project/tests/assert_country_name_overrides_still_needed.sql
  - .claude/active_work.md

impact_map: >
  writers: the seed is authored by hand; `dim_league.league_country` is written only by
    `base_apif__leagues` -> `base_apif__league_entity` -> `dim_league`. `RAW_APIF_LEAGUES` is
    written by `ingestion/api_football/loads/catalog.py:38` and is NOT touched here.

  downstream: `dbt ls --select base_apif__leagues+ --resource-type model` (dbt 1.7.19,
    .venv/Scripts/dbt.exe, run 2026-08-15) -> 16 models:
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

  blast_radius: THREE STRINGS in `dim_league.league_country`, on 3 of 45 rows (SPL, KL1, MLS).
    No mart number changes and no mart string changes: `grep -rn "league_country|country_flag_url"
    dbt_project/models/4_intermediate/ dbt_project/models/5_marts/` returns zero hits, so nothing
    downstream of `dim_league` reads the column yet. The 15 other downstream models are reached
    through the season/coverage columns, untouched here. No schema change — the column already
    exists with the same name and type.

  layer_rules: `scripts/check_layer_contract.py`. The correction goes in BASE, not in the core dim
    (`feedback_entity_corrections_in_base`: base prepares the override, the dim publishes; never
    `coalesce` in the dim) and not in staging, which stays a faithful 1:1 flatten. This mirrors
    `team_name_overrides` applied in `base_apif__teams_global.sql:50` exactly — seed + left join +
    `coalesce(override, provider)` + a singular test that fails when a row stops being a
    correction. Materialisation is a LAYER setting; no per-model override is added. No
    per-competition file, so the no-new-model rule is untouched.

  deploy_order: no ordering problem. Base is a TABLE, so corrected values appear on the next
    rebuild; until then `dim_league` keeps the provider spellings, which nothing reads. A dbt
    model and seed path are inside `.data_paths_prod`, so merging triggers `data:build:main` and
    prod picks it up on that run. The new singular test runs in the same build.

decisions_taken: >
  CPO ruling 2026-08-14 (`escalations.log`, ruling 2): "Our transformation layer is the place where
  we clean, reconcile and standardize the data. We can even impute missing information after
  researching properly... Raw doesn't define the taxonomies or categories or whatever. We do it in
  a way that makes sense for our purpose." Restated by the CPO 2026-08-15 in this conversation as
  "As said earlier, we standardize in base" — given in direct correction of my having offered the
  provider spellings as a display choice for him to make. It was not his to make; the rule already
  settled it.

  CPO ruling 2026-08-15, the one genuinely reserved item: `USA` renders as **United States of
  America**, his words verbatim. Copy is §10 and this is the only part of the change he decided.
  The other two rows are the same correction applied consistently: `Saudi-Arabia` -> `Saudi
  Arabia`, `South-Korea` -> `South Korea`.

  MEASURED, on the whole population (priced with `bq query --dry_run` first, 2,325,889 bytes):
  the provider returns 15 distinct country names for the 21 single-country competitions. Twelve
  need no correction (Argentina, Brazil, England, Finland, France, Germany, Italy, Japan, Mexico,
  Netherlands, Portugal, Spain). Three do, and they are the three rows of this seed.

  WHY A MAPPING SEED AND NOT A HYPHEN-TO-SPACE RULE. A pattern rule would look like the
  class-level fix and is actively wrong: `Guinea-Bissau` and `Timor-Leste` are correctly
  hyphenated country names, so a blanket replace corrupts them the moment either is onboarded. An
  explicit mapping cannot. The residual gap — a NEW multi-word country arriving hyphenated and
  nobody noticing — is closed by #69's foreign key, not by this seed, and that is stated in the
  seed description rather than left implied.

  NEW MECHANISM: none. This is `team_name_overrides` (seed + base join + still-needed test),
  applied to a second column, using the same three parts in the same layer.
  RECURRING COST: none material. One 3-row seed, one left join on a 45-row table, one test.

decisions_reserved:
  - Whether #69's `countries.csv` + `dim_country` eventually absorbs this seed or sits beside it,
    the way `team_name_overrides` sits beside `dim_team`. Not decided here; this seed is scoped to
    normalising the provider string and takes no position on the entity model.
  - The other three country columns (`dim_team.team_country`, `dim_player.player_birth_country`,
    `dim_coach.coach_birth_country`) almost certainly carry the same provider hyphenation across
    217/222/213 distinct values. NOT corrected here — that is #69's discovery step, and doing it
    blind from three known examples is the failure #69 exists to prevent.

done_when:
  - The seed carries exactly 3 rows, each with a `source` and a `note`.
  - `base_apif__leagues.sql` applies it by left join + coalesce; `dim_league.sql` is UNCHANGED.
  - `dbt parse` succeeds; SQLFluff is clean on both changed .sql files, full rule set, from root.
  - The still-needed test is shown RED first by proving it fires on a no-op row, then green.
  - Verified against RAW, priced first: the 21 single-country competitions yield 15 distinct names
    with `Saudi Arabia`, `South Korea` and `United States of America` among them and no hyphen.
  - The two stale claims from the last task are corrected: the #62 note and `active_work.md` both
    say the rendered string is a §10 decision blocking step 3. It is not.

amendments: (none)
