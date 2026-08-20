---
name: validate-local
description: |
  Run the same quality gates CI runs, locally, BEFORE pushing — so a PR doesn't
  bounce off CI and turn into fix-after-CI churn. Mirrors `.gitlab-ci.yml`'s
  `validate:governance`, `validate:ui`, `validate:secrets` and `test:python` jobs.
  Use before `git push` / opening an MR, after a set of changes, or whenever you
  want to know if CI will pass.

  Do NOT use to run the full BigQuery data build (dbt build + DQ tests) — that is
  expensive and runs in `data:build:mr`. This skill runs the fast offline gates
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
  `data:build:mr` (see Tier 3 below); a full local `dbt build` is expensive.

## The gates (run in order; stop and report on first hard failure)

### Tier 1 — fast, offline (always run)

These need no credentials and finish in seconds. They mirror `.gitlab-ci.yml`'s
`validate:governance` (layer contract, registry sync, competition-type seed, copy
gate, task artifacts), `validate:ui` (i18n + metric manifests) and `test:python`
(unit tests).

**Six of these also run at turn end** via `stop_gate.py`'s `FAST_GATES`, named
explicitly because "the first N" drifts the moment the list is reordered.

⚠ That count is PROSE and the pinning test does not check it — it asserts set
equality over the marked block below, so this sentence went stale the moment a
sixth gate was added and nothing caught it. If you add a gate, change this number
too.

The markers below are load-bearing: `test_fast_gates_and_validate_local_agree`
extracts the names BETWEEN them and asserts SET EQUALITY with `FAST_GATES`. Do not
remove them, and do not edit the list without editing the tuple. An earlier version
of that test only checked each name appeared *somewhere* in this file — which every
one does, three times over — so it stayed green when this very line was deleted, and
green against the broken form it was written to catch (platform-reviewer, opus).

<!-- FAST_GATES:START -->
`check_layer_contract` · `check_registry_var_sync` · `check_competition_type_seed` · `check_ui_i18n_metrics` · `check_copy_gate` · `check_description_hygiene`
<!-- FAST_GATES:END -->

**`check_task_artifacts.py` is deliberately NOT one of them.** It needs a fetched
base branch (the CI job sets `GIT_DEPTH: 0` for exactly that) and it hard-fails on
a missing or stale `review.md` — so at turn end it would block every turn during the
build phase, before the review cycle has even run. It belongs here and in CI, not in
the hook.

`stop_gate.py` is the source of truth for that set;
`test_fast_gates_and_validate_local_agree` pins the two files against each other.

```bash
python scripts/check_layer_contract.py
python scripts/check_registry_var_sync.py
python scripts/check_competition_type_seed.py
python scripts/check_copy_gate.py
python scripts/check_description_hygiene.py
python scripts/check_task_artifacts.py
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

`dbt parse` mirrors `validate:governance`; `sqlfluff lint` mirrors `data:build:mr`'s lint
step. Both use the dbt templater, which compiles Jinja against the warehouse, so
they need a working BigQuery profile (ADC / `gcloud auth`). Skip with a note if
unauthenticated.

```bash
cd dbt_project && dbt deps && dbt parse
sqlfluff lint models        # from inside dbt_project/
```

### Tier 3 — full data build + DQ tests (CI-only by default)

`dbt build` materialises every model and runs all data-quality tests against
BigQuery. This is what `data:build:mr` does on the MR. Do NOT run the full build
routinely — it is slow and costs query bytes. If you specifically need to verify
data-quality on changed models locally and you are authed:

```bash
cd dbt_project && dbt build --select state:modified+ --defer --state ./ci_state
```

Otherwise rely on the `data:build:mr` job on the MR. Data quality is
non-negotiable (working_agreement.md §7) — never report a change as verified on
the strength of Tier 1+2 alone if it touches metric logic; let `data:build:mr`
run, or run the scoped build above.

## Reporting

After running, summarise one line per gate: `PASS` / `FAIL` (with the first
error) / `SKIPPED (no BigQuery auth)`. If any Tier 1 or Tier 2 gate fails, fix
it before pushing — that failure would have turned into a red CI check.

## Mapping to CI (so this stays in sync)

GitLab job names since the 2026-08 migration. The GitHub workflow names this table
used to carry (`ci-validate`, `ci-ui`, `python-ci`, `ci-data-build`) are dormant —
GitHub Actions run nothing — so citing them here was a live-looking claim about a
pipeline that does not run.

| Gate | `.gitlab-ci.yml` job |
|---|---|
| `check_layer_contract.py` | `validate:governance` |
| `check_registry_var_sync.py` | `validate:governance` |
| `check_competition_type_seed.py` | `validate:governance` |
| `check_copy_gate.py` | `validate:governance` |
| `check_description_hygiene.py` | `validate:governance` |
| `check_task_artifacts.py` | `validate:governance` (needs `GIT_DEPTH: 0`) |
| `dbt deps` + `dbt parse` | `validate:governance` |
| `check_ui_i18n_metrics.py` + JSON validity | `validate:ui` |
| `pytest tests/` | `test:python` |
| gitleaks secret scan | `validate:secrets` |
| `sqlfluff lint models` | `data:build:mr` |
| `dbt build` + DQ tests | `data:build:mr` (MR) / `data:build:main` (main) |

If a CI workflow adds or changes a gate, update this list so local validation
stays a faithful mirror.
