# Task contract — dim_country + dim_region (#69 step 3)

objective: >
  Publish the two dimensions #69's rescope calls for. `dim_country` is genuinely new: countries
  exist nowhere in the model layer today, only as free text in four dims. `dim_region` publishes
  `confederations.csv`, which has existed since #57 and is read by nothing. Together they let a
  competition POINT AT one or the other, so which relationship is populated is the answer and no
  `single_country` flag is needed.
  ⚠ THIS UNIT IS THE DIMS ONLY. The foreign keys from the four free-text columns are #69 step 5
  and a separate MR — a dim and its first reader cannot ship together, the same rule that keeps
  #62 step 3 apart from step 1.
refs: GitLab #69 (rescope + the naming rulings), #62 step 3 (the page that needs `dim_country`)

scope_paths:
  - dbt_project/seeds/countries.csv
  - dbt_project/seeds/schema.yml
  - dbt_project/models/3_core/dim_country.sql
  - dbt_project/models/3_core/dim_region.sql
  - dbt_project/models/3_core/core.yml
  - dbt_project/docs/layering.md

impact_map: >
  writers: both dims are NEW and seed-published. `countries.csv` is authored here from #69's
    recorded discovery; `confederations.csv` already exists and is NOT edited.

  downstream: NONE — both are LEAVES. Nothing reads either until #69 step 5 adds the foreign keys
    and #62 step 3 builds `mart_competition_index`. Deliberate: this is the "additive and not yet
    read" pattern `confederations.csv` itself shipped under in #57, and the same reason
    `mart_competition_index` is parked rather than built.

  blast_radius: NONE on any existing number, string or row. No existing model is modified. The diff
    adds two models, one seed and their schema entries; it touches no file under `2_base/`,
    `4_intermediate/` or `5_marts/` and no existing `3_core` model.

  ⚠ WHAT dim_region DOES AND DOES NOT ADD, stated because it is easy to overstate:
    `competition_registry.confederation` ALREADY carries a `relationships` test to
    `ref('confederations')` (`dbt_project/seeds/schema.yml:188`), so the competition->region guard
    exists today at seed level. `dim_region` buys PUBLICATION and SYMMETRY with `dim_country`, not
    a new guard. The symmetry is the point of the rescope — two relationships of the same kind —
    but calling it a new safety net would be false.

  layer_rules: `scripts/check_layer_contract.py`. Both are core dims published from seeds, which is
    the layer's job: seeds author, `3_core` publishes. Neither derives a fact. No per-competition
    file and no `league_code` involvement, so the no-new-model rule is untouched. Materialisation
    follows the layer setting in `dbt_project.yml`; no per-model override.

  deploy_order: additive and order-free. `dbt seed` runs before models in every build path, and
    both dims are leaves so they can be built before a reader exists. A seed and a `3_core` model
    path are inside `.data_paths_prod`, so merging triggers `data:build:main` and the tables appear
    on that run.

decisions_taken: >
  CPO rescope of #69, 2026-08-16 (its note is the authority): "dim_region from confederations.csv
  (publish what exists) + dim_country built new. A competition POINTS AT one; which relationship is
  populated IS the answer." And on the modelling this replaces: "You don't mix up countries and
  continents or regions in one column and add a flag 'single country'. That's really bad modeling."

  `countries.csv` CONTENT is the 224-entity canonical list from #69's discovery, under the four
  naming rulings of 2026-08-16 recorded in `escalations.log`: English, everyday short form, no
  diacritics, with `Republic of Ireland` and `United States of America` as the two stated
  exceptions.

  VERIFIED AGAINST CURRENT PROD BEFORE AUTHORING, priced first (3,681,429 bytes): 284 distinct
  provider country strings across the four staging surfaces today; excluding the `World` sentinel,
  **283 of 283 resolve into the 224 via `country_name_overrides`** — nothing uncovered. That check
  matters because #69 step 5's foreign keys will fail on anything this seed misses, and it was run
  against today's data rather than reused from the 08-16 discovery.

  NEW MECHANISM: none. Two seed-published dims, the shape `dim_league` and the other core dims
  already use.
  RECURRING COST: negligible. A 224-row table and a 7-row table built once per run.

decisions_reserved:
  - `entity_type` (un_state / association / territory / historical) is NOT a column. The CPO on
    being shown a 7-column draft: "we only need a mapping between what the provider gives us and
    what we turn into the single source of truth name". The distinction is preserved in #69's
    discovery note if a consumer ever needs it; nothing needs it to render a country name.
  - `label_i18n_key` per country is NOT a column — 224 keys x 3 locales is a copy cost and the
    CPO's to authorise. `dim_region` HAS one only because `confederations.csv` already shipped with
    it.
  - Confederation per country is NOT a column, and there is NO SOURCE for it: the registry gives
    confederation per COMPETITION and the UN list the CPO supplied has none. ⚠ It is also not
    needed — the competitions page takes the region from the competition's own `confederation`,
    never from the country's.
  - The four foreign keys (#69 step 5), and whether `dim_country` supersedes
    `country_name_overrides` or sits beside it as `team_name_overrides` sits beside `dim_team`.
  - Whether the registry's `country` field is blanked for the 24 competitions holding a region
    word. #69 names it; it changes what the export renders and belongs with step 4.

done_when:
  - `countries.csv` carries 224 rows; `country_key` unique; no `country_name` with a diacritic.
  - Both dims exist in `3_core`, are pass-throughs of their seed, and derive nothing.
  - `dbt parse` succeeds; SQLFluff clean on both new .sql files, full rule set, from the repo root.
  - `dbt ls --select dim_country+ dim_region+ --resource-type model` shows both are LEAVES.
  - `core.yml` documents both with not_null + unique on the keys.
  - `check_layer_contract.py` and `check_registry_var_sync.py` pass.

amendments:
  - 2026-08-17: + dbt_project/docs/layering.md — authority: scope-auditor FAIL, round 1, finding 2.
    content: `layering.md`'s "Attribute masquerading as entity" bullet names COUNTRY explicitly —
    "keep as attributes until a consumer needs rollups or hierarchies (e.g. continent,
    confederation, position group). Promote to a dim when the rollup logic appears, not before."
    This MR promotes country AND region to dims while stating in three places that nothing reads
    them, and the rollup the doc names as the trigger — confederation on the country — is precisely
    what this task leaves out for want of a source. So the doc's condition is NOT met; the doc is
    being OVERRIDDEN by the CPO's design. The reviewer was right that an unrecorded override plus
    an unchanged doc is a doc-sync failure: the next reader would find a rule and a violation with
    nothing connecting them. The bullet gains a pointer to the ruling. The RULE IS NOT WEAKENED —
    it still says promote on the rollup, and the exception names its authority rather than
    generalising.
