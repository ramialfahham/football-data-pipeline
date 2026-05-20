## Cursor Cloud specific instructions

### Services overview

| Component | What it does | Can run without GCP? |
|-----------|-------------|---------------------|
| **Python tests** (`pytest tests/ -v`) | Unit tests for ingestion logic; all BQ calls are mocked | Yes |
| **dbt parse** (`dbt parse --project-dir dbt_project`) | Syntax-checks all dbt models without touching BigQuery | Yes |
| **SQLFluff** (`sqlfluff lint models/<path>` from `dbt_project/`) | SQL linting; uses dbt templater which requires BQ credentials | No |
| **dbt build/run** | Builds models in BigQuery | No |
| **Ingestion** (`python -m ingestion.api_football.main`) | Calls API-Football and loads into BigQuery | No (needs `API_FOOTBALL_API_KEY` + GCP auth) |
| **Static site** (`python -m http.server 8080` from `site/`) | Matchday IQ landing page + sub-pages | Yes (data pages show "not available" without exported JSON) |

### Activation

Always activate the venv before any command:

```bash
source /workspace/.venv/bin/activate
```

### Running tests and checks (no GCP required)

```bash
# Python unit tests (92 tests, all mock BQ)
python -m pytest tests/ -v

# dbt syntax check (no BQ connection needed)
dbt parse --project-dir dbt_project

# pre-commit hooks (secret scanning, large files, merge conflicts)
pre-commit run --all-files
```

### Commands that require GCP credentials

These fail without Application Default Credentials or a service account:

- `dbt build --project-dir dbt_project` (and any `dbt run/test/snapshot`)
- `sqlfluff lint models/<path>` from `dbt_project/` (the dbt templater calls `dbt compile` which connects to BQ)
- `python -m ingestion.api_football.main` (also needs `API_FOOTBALL_API_KEY`)

### Gotchas

- **`GOOGLE_APPLICATION_CREDENTIALS` must be a file path to a service account JSON**, not the JSON content itself or an API key. The `google.auth.default()` library reads this env var as a file path. If you have JSON content, write it to a file first and set the env var to that file path. Example: `echo "$GCP_SA_KEY_JSON" > /tmp/sa.json && export GOOGLE_APPLICATION_CREDENTIALS=/tmp/sa.json`.
- **SQLFluff requires BigQuery auth.** The `.sqlfluff` config uses `templater = dbt`, which invokes `dbt compile` internally. Without GCP credentials, linting fails. There is no local-only fallback configured.
- **dbt profiles.yml is not committed.** The update script copies `profiles.example.yml` to `~/.dbt/profiles.yml` only if one doesn't already exist. The profile uses `method: oauth` (GCP ADC).
- **Run SQLFluff from `dbt_project/`**, not the repo root, so the dbt templater picks up `.sqlfluff`.
- **`dbt_project.yml` warning about unused snapshot config** is benign — it fires because no snapshot models are currently defined under that path.
- **Python 3.12** works with the current dependency set despite the README mentioning 3.11.
- **`core.hooksPath`** may be set in the git config, blocking `pre-commit install`. Run `git config --unset-all core.hooksPath` first if you see "Cowardly refusing to install hooks."
