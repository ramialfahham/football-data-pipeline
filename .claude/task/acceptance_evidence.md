# Acceptance evidence — one authoritative competition name, corrected in base

⭐ **THIS IS THE WAREHOUSE HALF OF #55**, which specified this exact fix 24 days before the work
started: *"One field, in the warehouse, that every surface reads. Published by `dim_league`, with
corrections applied in base… The registry keeps what it is good at and stops carrying a display
name."* The contract was written against the defect rather than against #55 because the issue was
not found until after the build; recorded here rather than restated, since the contract may not be
edited on a dirty tree. #106 was filed and CLOSED as a duplicate of #55.

⚠ **THE SEED'S METHOD HAS A KNOWN LIMIT, and it is not theoretical.** The 20 rows were derived from
where the registry and the provider DISAGREE. #55 proves that is insufficient: `UECL` was stale in
BOTH sources, so they agreed and were both wrong (UEFA dropped "Europa" in 2024). It is in the seed
only because #55 had caught it by hand. Among the 28 competitions left on the provider name there
may be more stale-but-agreeing names; nothing has checked them against an external record. That
pass belongs to **#55**, which already states the discipline and names #850 as the model.

⚠ **BL1 is not in the seed, and BL2 is not in it for a DIFFERENT reason.** Do not merge the two.
  · **BL1** — #55 rules the name is "Bundesliga" and the provider already sends exactly that, so an
    override row would equal the provider value and
    `assert_league_name_overrides_are_corrections` would fail it as STALE. The wrong value is the
    REGISTRY's long legal form, which reaches the home page through the export rather than through
    `dim_league`; that is #55's export half, not a row here.
  · **BL2** — NOTHING has ruled it. Its two sources disagree ("2. Fußball-Bundesliga" vs
    "2. Bundesliga"), so the seed's own inclusion test flags it, and I left it alone rather than
    pick a competition's name. It sits with the other unverified names under #55.
⛔ An earlier version of this passage said "BL1 and BL2 are deliberately NOT in the seed" and
credited one ruling for both. `scope-auditor` FAILed that in `contract.md` twice; it survived HERE
because I corrected the line each reviewer named instead of sweeping the class
(`feedback_fix_the_class_not_the_instance`). Found by `analytics-engineer-reviewer` in round 3, out
of its own remit.

## The defect, measured on LIVE PRODUCTION data before any change

```
$ bq query --use_legacy_sql=false \
  'select competition_name, count(*) as competitions_sharing_the_name,
          string_agg(league_code order by league_code) as league_codes
   from `football-data-pipeline-gcp.marts.mart_competition_index`
   where competition_name is not null
   group by competition_name having count(*) > 1'

+------------------+-------------------------------+--------------+
| competition_name | competitions_sharing_the_name | league_codes |
+------------------+-------------------------------+--------------+
| Serie A          |                             2 | BSA,SA       |
+------------------+-------------------------------+--------------+
```

API-Football sends `Serie A` for Brazil's Brasileirão as well as Italy's Serie A. Because
`mart_competition_index.competition_name` drives a competition page's `<title>`, `<meta
description>` and `<h1>`, two competitions produced byte-identical SEO surfaces. The site's own
audit refused the build rather than shipping them, which is how this was found.

It was already visible without a competition page: `dist/en/competitions/index.html` renders
"Serie A" twice and contains the word "Brasileirão" nowhere.

## The divergence behind it, measured both directions

Two sources fed competition names, and they disagreed for **21 of 48** competitions (27 agreed):

| | Home page | Competitions page |
|---|---|---|
| source | registry `name`, read by the export | provider name, via `dim_league` |
| DFBP | `DFB-Pokal` | `DFB Pokal` |
| SPL | `Saudi Pro League` | `Pro League` |

Both strings are in the built output at `site_v2/dist/`. Verified with
`grep -o "DFB[- ]Pokal" dist/en/index.html` → `DFB-Pokal` and the same grep on
`dist/en/competitions/index.html` → `DFB Pokal`.

## criteria_demonstrated:

  - **The seed corrects exactly the competitions whose provider name we do not show, and no
    others.** Measured against live `stg_apif__leagues`: **20 corrected, 28 left on the provider
    name, 48 total.** Two-sided, so an over-correction would show as a shrunk right-hand number.
    (It read 21/27 before BL1 and BL2 came out and `UECL` went in.)
  - **`assert_competition_name_is_unique` is RED before the change and GREEN after.** Before is
    not a simulation — it is the `bq` result above, run against prod. After is the same predicate
    over `coalesce(override, provider)`:
    `BEFORE -> RED {'Serie A': ['BSA', 'SA']}` · `AFTER -> GREEN`.
  - **`assert_league_name_overrides_are_corrections` fires on BOTH its branches, watched red.**
    Evaluated against live provider data:
    `1. the seed as committed -> GREEN (0 rows)`
    `2. MUTATED: a league_code that does not exist -> RED (1 row)  ORPHAN NOPE`
    `3. MUTATED: BSA set to the provider's own name -> RED (1 row)  STALE BSA`
    A test that only ever passes proves nothing; both branches were made to fail on purpose first.
  - **No name shown to a reader changes.** Every seed value is the name already authored in
    `docs/competition_registry.yml` and already served to the registry-fed pages. The change makes
    the provider-fed pages agree with them; it introduces no new wording.
  - **The join cannot fan out the row count.** `league_name_overrides.league_code` carries dbt's
    `unique` and `not_null` tests, registered in the graph as
    `football_data_pipeline.unique_league_name_overrides_league_code`.
  - **The correction sits in base and the dim still publishes.** `dim_league.sql` is unchanged and
    contains no coalesce; the coalesce is in `base_apif__leagues.sql` beside the country one that
    was already there.

## Gates

```
python scripts/check_registry_var_sync.py     OK (48 competitions; 48 rows over 9 columns)
python scripts/check_description_hygiene.py   ok (1629 descriptions, rendered lengths within 1024/16384)
python -m sqlfluff lint <the 3 changed/added SQL files>  All Finished!  (repo root, jinja, bigquery)
.venv/Scripts/dbt.exe parse                   OK
.venv/Scripts/dbt.exe ls --select league_name_overrides+   seed reaches the graph
python -m pytest tests/ -q                    1010 passed, 1 skipped, 14 subtests
```

⚠ `check_description_hygiene` FAILED first, and correctly: the seed description carried an ISO
date, the word "CPO" and a severity emoji. dbt descriptions are published to BigQuery columns and
read by strangers, so the standard bans all three. Rewritten to state what the data means.

## What this does NOT do

- **It does not change the frontend today.** Prod picks the seed up on the next `fdp-nightly`
  (04:00 UTC); the committed `site_v2/src/data/competition_index.json` still holds the old names
  until re-exported. `feat/navigation-rules-competition-shell` stays blocked until merge → nightly
  → re-export.
- **It does not remove the second source.** The export still reads registry `name` at
  `export_site_data.py:944, 995, 1078, 1206`. Seeding the override makes the two AGREE, which is
  why nothing a reader sees changes; making the export read the warehouse is the filed follow-up.
- **It does not touch the other two `league_name` paths.** `stg_apif__fixtures_next:35` and
  `stg_apif__standings:30` carry their own copies. No mart reads either, so no page renders them
  today — recorded because "the league name is fixed" would otherwise be a false blanket claim.
