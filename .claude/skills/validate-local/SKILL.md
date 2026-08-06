---
name: validate-local
description: |
  Run the same quality gates CI runs, locally, BEFORE pushing — so a PR doesn't
  bounce off CI and turn into fix-after-CI churn. Mirrors the ci-validate,
  python-ci, and ci-ui workflows. Use before `git push` / opening a PR, after a
  set of changes, or whenever you want to know if CI will pass.

  Do NOT use to run the full BigQuery data build (dbt build + DQ tests) — that
  is expensive and runs in ci-data-build. This skill runs the fast offline gates
  plus dbt parse and SQL lint.
---

# validate-local

Run the CI gates locally and report pass/fail per gate. The point is to catch
failures here, in seconds, instead of after a push → CI run → red check → fix
commit round trip (the dominant source of `fix:` churn in this repo's history).

## When to use

- Before `git push` or `glab mr create`.
- After finishing a unit of work, to confirm it's CI-clean.
- When a hook (pre-push) or the user asks "will CI pass?".

## When NOT to use

- You only need one specific check — just run that script directly.
- You want the full warehouse build / data-quality tests — those run in
  `ci-data-build` (see Tier 3 below); a full local `dbt build` is expensive.

## The gates (run in order; stop and report on first hard failure)

### Tier 1 — fast, offline (always run)

These need no credentials and finish in seconds. They mirror `ci-validate`
(layer contract + registry sync), `ci-ui` (i18n + metric manifests), and
`python-ci` (unit tests).

```bash
python scripts/check_layer_contract.py
python scripts/check_registry_var_sync.py
python scripts/check_competition_type_seed.py
python scripts/check_task_artifacts.py --base origin/main
python scripts/check_ui_i18n_metrics.py
python -m json.tool site/i18n/en.json > /dev/null
python -m json.tool site/i18n/de.json > /dev/null
python -m json.tool site/i18n/fi.json > /dev/null
python -m json.tool site/match-preview/metric_manifest.json > /dev/null
python -m json.tool site/match-preview/metric_definitions.json > /dev/null
python -m pytest tests/ -q
```

Expected: `check_layer_contract.py` prints `Layer contract checks passed.`;
`check_registry_var_sync.py` prints `OK (N competitions)`; pytest is all-green.

### Tier 2 — needs BigQuery auth (run if `bq` works locally)

`dbt parse` mirrors `ci-validate`; `sqlfluff lint` mirrors `ci-data-build`'s lint
step. Both use the dbt templater, which compiles Jinja against the warehouse, so
they need a working BigQuery profile (ADC / `gcloud auth`). Skip with a note if
unauthenticated.

```bash
cd dbt_project && dbt deps && dbt parse
sqlfluff lint models        # from inside dbt_project/
```

### Tier 3 — full data build + DQ tests (CI-only by default)

`dbt build` materialises every model and runs all data-quality tests against
BigQuery. This is what `ci-data-build` does on the PR. Do NOT run the full build
routinely — it is slow and costs query bytes. If you specifically need to verify
data-quality on changed models locally and you are authed:

```bash
cd dbt_project && dbt build --select state:modified+ --defer --state ./ci_state
```

Otherwise rely on the `ci-data-build` check on the PR. Data quality is
non-negotiable (working_agreement.md §7) — never report a change as verified on
the strength of Tier 1+2 alone if it touches metric logic; let `ci-data-build`
run, or run the scoped build above.

## Reporting

After running, summarise one line per gate: `PASS` / `FAIL` (with the first
error) / `SKIPPED (no BigQuery auth)`. If any Tier 1 or Tier 2 gate fails, fix
it before pushing — that failure would have turned into a red CI check.

## Mapping to CI (so this stays in sync)

| Gate | CI workflow / step |
|---|---|
| `check_layer_contract.py` | ci-validate → Enforce layer contract |
| `check_registry_var_sync.py` | ci-validate → Check registry/var sync |
| `check_competition_type_seed.py` | ci-validate → Check competition-type seed coverage |
| `check_task_artifacts.py` | ci-validate → Check governance task artifacts |
| `dbt deps` + `dbt parse` | ci-validate → dbt deps / Parse project |
| `check_ui_i18n_metrics.py` + JSON validity | ci-ui |
| `pytest tests/` | python-ci |
| `sqlfluff lint models` | ci-data-build → Lint SQL |
| `dbt build` + DQ tests | ci-data-build → dbt build |

If a CI workflow adds or changes a gate, update this list so local validation
stays a faithful mirror.
