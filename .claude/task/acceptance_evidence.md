# Acceptance evidence — MR6, `persist_docs` + published dbt docs

> One line per declared criterion in `contract.md`, each read from an actually-executed command and
> from its OUTPUT rather than its exit code. Where the claim is about BigQuery, the evidence is read
> back off BigQuery, not off the YAML that was supposed to produce it.
>
> ⚠ THE BULLETS BELOW ARE INDENTED 2sp ON PURPOSE. `_block()` in `git_discipline.py` collects lines
> under `criteria_demonstrated:` until the first NON-INDENTED non-empty line, so a bullet at column
> zero terminates the block immediately and the gate reads ZERO criteria.

criteria_demonstrated:

  - `persist_docs` reaches EVERY model and EVERY seed, set once at project level. Read out of
    `target/manifest.json` after `dbt parse`, grouping every node by its resolved config:
    `model persist_docs={"columns": true, "relation": true} count=97` and
    `seed ... count=9`, with `NOT fully enabled: none`. Counted from the manifest rather than
    inferred from the YAML nesting, because the nesting is exactly what could be wrong.
  - The new `seeds:` block relocated NOTHING. All 9 seeds still resolve to `schema=dev_scratch`
    with `custom=None`, i.e. they still ride `target.schema` through
    `macros/generate_schema_name.sql`. This is the one way this MR could have silently broken every
    `ref()` to a seed, so it is checked explicitly rather than assumed from "I did not add
    `+schema`".
  - Seed descriptions actually land in BigQuery, byte-for-byte. `dbt seed --select
    competition_types --target dev` (`OK loaded seed file dev_scratch.competition_types INSERT 14`),
    then the live table read back through the BigQuery client with an explicit utf-8 decode:
    relation 580 chars identical, and all 5 columns identical
    (`competition_type` 85, `entity_type` 61, `display_group` 378, `label_i18n_key` 453,
    `label_en` 495). Non-ASCII characters survived the round trip, checked because this repo has
    been bitten by a pipe mangling UTF-8 before.
  - Model relation descriptions land too. `dbt run --select stg_apif__leagues --target dev`
    (`CREATE TABLE (509.0 rows, 2.4 MiB processed)`), then the same read-back:
    `manifest 147 chars / bigquery 147 chars / identical: True`.
  - Model COLUMN descriptions land. ⚠ This could NOT be proven locally, and the gap was recorded
    as open rather than papered over: no staging model declares a single column description (0 of
    15, measured off the manifest), and every model that does is core-and-downstream, needing the
    whole chain built into dev.
    NOW CLOSED off this MR's own pipeline (`!89`, pipeline 2778903367, `data:build:mr` 555s,
    green). `bq show --schema football-data-pipeline-gcp:ci_core.dim_league` reads back a 169-char
    table description and **9 of 9 columns described**, including the two that come from shared
    docs blocks rather than inline YAML — `league_sk` 172 chars and `league_code` 315 chars, which
    is the `{{ doc() }}` path resolving all the way into BigQuery column metadata.
  - THE PREDICTED ONE-TIME COST HAPPENED, and was read from the log rather than assumed. The
    contract predicted that changing `dbt_project.yml` alters every model's config, so
    `state:modified` matches all 97 models and this MR's `data:build:mr` rebuilds the whole `ci_*`
    warehouse once. The job reports `Found 97 models, 936 tests, 9 seeds` and
    `Done. PASS=1039 WARN=1 ERROR=0 SKIP=0 TOTAL=1040` — the full selection, not an incremental
    subset. The single WARN is the pre-existing `accepted_values_fct_fixture_status_short__…`
    data-quality test in `models/3_core/core.yml`, which is unrelated to this MR and warns on main
    too; ERROR=0.
    All six jobs green: `validate:governance` 47s, `validate:secrets` 19s, `lint:python` 12s,
    `test:python` 57s, `build:site-v2` 22s, `data:build:mr` 555s.
  - `dbt docs generate --static --target prod` is a real command on this dbt version, and produces
    all three artifacts. Run against dev: `Catalog written to ...target\catalog.json`, leaving
    `static_index.html` (6,633,926 bytes, self-contained), `manifest.json` and a NON-empty
    `catalog.json` — 10 nodes, 11 sources, 78 columns, `empty: False`, and `comment=True` on the
    nodes, i.e. the persisted descriptions are visible in the catalog.
    ⚠ First attempt FAILED, and the failure is recorded because it is informative: `docs generate`
    compiles, and `assert_metric_catalogue_expr_resolvable` needs `dev_scratch.metric_catalogue`,
    which my dev target had never held. It is a property of an empty dev environment, not of this
    change — in CI the step runs after a full prod build, so every table exists. Cleared by seeding
    all 9 seeds to dev and re-running.
  - THE HAZARD IS SEEN RED, bracketed on a live table rather than cited from documentation.
    Against `dev_scratch.competition_types` via the same `client.update_table` call dbt makes:
    column description 1,024 chars ACCEPTED, 1,025 REJECTED (`400 PATCH ... The description for
    field label_en is too long`), 2,000 REJECTED; table description 16,384 ACCEPTED, 16,385
    REJECTED. One character over is a hard rejection, not a truncation. Both descriptions were
    restored afterwards and the restore was verified (`restored: True` for table and column).
  - dbt does NOT swallow that rejection, so an escape would be LOUD. `bigquery__persist_docs`
    (`dbt/include/bigquery/macros/adapters.sql:99`) delegates to `adapter.update_columns`, which
    ends in a bare `conn.handle.update_table(new_table, ["schema"])`
    (`dbt/adapters/bigquery/impl.py:609`) with no try/except — the exact call proven to raise
    above. The relation description is not set there at all: the macro's own comment says it is
    "handled in the CTAs statement", so an over-long table description fails the CREATE TABLE.
  - Every rendered description is inside BigQuery's limits, measured on the RENDERED text so a
    docs block counts as what it resolves to: 106 relation descriptions longest 601 against 16,384;
    870 column descriptions longest 588 against 1,024; `over limit: 0` for both; 9 of 9 docs blocks
    resolved with zero unrendered `{{ doc(` surviving into the manifest.
    ⚠ Taken from the manifest, NOT from the gate, deliberately — the gate currently in main skips
    the length check entirely on a bare `{{ doc() }}` reference, so it cannot be the evidence for
    the claim it is blind to.
  - The five offline gates pass, read from their output: `Layer contract checks passed.`,
    `check_registry_var_sync: OK (48 competitions; 48 registry-seed rows over 8 columns).`,
    `check_competition_type_seed: OK (8 registry type(s) all present in seed of 14).`,
    `COPY GATE ok: 432 strings across 3 locales`, and
    `DESCRIPTION HYGIENE ok: 618 descriptions across 19 files, 6 rules, none over 600 chars`.
  - `.gitlab-ci.yml` still parses and gained no job. Parsed with `yaml.safe_load`: the 13 job names
    are unchanged, `data:build:main`'s script now ends `dbt docs generate --static --target prod`,
    its `artifacts` block lists the three target files with `expire_in: 30 days`, `allow_failure`
    is absent, and its `rules` are byte-identical to before.
  - `dbt parse` is clean. The only warning is the pre-existing
    `unused configuration paths: snapshots.football_data_pipeline`, which was present before this
    change and is the dormant snapshots block. The new `seeds:` block is NOT reported unused, which
    is how we know it binds.
  - `python -m pytest tests/` — `863 passed, 1 skipped, 14 subtests passed in 531.74s`, which is
    the 853 measured before round 2 plus the 10 new pins. Measured, not predicted (#904). No file
    was edited while the suite was running.
  - The handover rides in this commit and fits its cap: 15,996 characters against the 16,000 limit
    in `handover_in.py:46`, measured with Python `len()` rather than `wc -c`.
  - EVERY INVARIANT THIS MR ESTABLISHES IS PINNED, AND EVERY PIN WAS SEEN RED. Added in round 2
    after platform-reviewer FAILed and was right: nothing in `tests/` referenced `persist_docs`,
    `docs generate`, `catalog.json` or `static_index`, so the whole MR could be reverted green.
    `tests/test_persist_docs_policy.py` now holds 10 assertions, and each was driven red by a
    REALISTIC regression rather than a syntax error, then restored:
      `persist_docs removed from models` RED · `seeds block deleted` RED ·
      `+schema added to seeds (the silent relocation)` RED · `a layer turns persist_docs off` RED ·
      `docs step moved to data:build:mr` RED · `--static dropped` RED ·
      `allow_failure restored` RED · `catalog.json dropped from artifacts` RED.
    Both mutated files were restored from a byte backup and the restore verified by sha256 before
    the next mutation ran; `git diff --stat` afterwards shows insertions only, and the sole
    `allow_failure` string left in the tree is the comment explaining its absence — which is
    exactly why the test parses YAML instead of grepping text.
  - THE ARTIFACT AT PRODUCTION SCALE, which round 1 asserted from a dev-scale figure.
    platform-reviewer's second finding was half right and its premise was wrong, and both halves
    are recorded because the correction is the useful part.
    WRONG: the claim that 6.6 MB would grow ~10x. `target/manifest.json` is 5,085,350 bytes and is
    a PARSE artifact holding all 97 models and 9 seeds regardless of what was built, so the biggest
    payload embedded in `static_index.html` was ALREADY at production scale in the dev run. The
    dbt docs SPA bundle (1,501,065 bytes) is fixed. Only the catalog scales, at ~424 bytes/column.
    RIGHT, and now closed: no estimate and no limit check existed. Measured from free BigQuery
    table metadata — prod holds 410 tables / 8,804 columns across the five bare datasets. Costed
    at that ceiling: catalog ~3.7 MB, `static_index.html` ~10.3 MB, total upload ~19.1 MB against
    gitlab.com's 1 GB per-job maximum, about 1.9% of it. The warehouse would need to grow ~52x
    before this is a question.
    ⚠ That 8,804 is a deliberate UPPER BOUND: it counts every table in those datasets, but
    `dbt/task/generate.py:128` (`if key in node_map`) drops any relation dbt cannot map to a
    manifest node, so the real catalog covers only the ~106 dbt-managed relations. The true figure
    is smaller than the number defended here.
    ⚠ SEPARATELY, and NOT fixed here: counting those tables showed prod's `staging` dataset holds
    259 relations against 15 staging models — ~244 orphaned VIEWS from the banned per-competition
    pattern (`stg_apif__bl1_fixture_events`, `stg_apif__bl1_predictions`, …), including entities
    the project no longer models. The repo forbids the pattern and `check_layer_contract.py`
    enforces it, but the guard governs the repo and not the warehouse. Filed as its own task
    rather than folded into this MR; dropping production relations is the CPO's call.
