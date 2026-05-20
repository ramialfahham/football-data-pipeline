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

### GCP credential setup

The `GOOGLE_APPLICATION_CREDENTIALS` secret must contain the **full JSON content** of a GCP service account key (not a key ID or API key). On session start, write it to a file and configure dbt:

```bash
python3 -c "
import os, json
creds = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', '')
if creds.strip().startswith('{'):
    os.makedirs('/home/ubuntu/.config/gcloud', exist_ok=True)
    path = '/home/ubuntu/.config/gcloud/service-account.json'
    with open(path, 'w') as f:
        f.write(creds)
    print(f'Wrote SA key to {path}')
"
export GOOGLE_APPLICATION_CREDENTIALS=/home/ubuntu/.config/gcloud/service-account.json
```

The dbt profile at `~/.dbt/profiles.yml` must use `method: service-account` with `keyfile` pointing to this file (not `method: oauth`). The update script copies `profiles.example.yml` (which uses oauth) — you need to override it for Cloud Agent use.

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

These fail without a valid service account JSON written to disk:

- `dbt build --project-dir dbt_project` (and any `dbt run/test/snapshot`)
- `sqlfluff lint models/<path>` from `dbt_project/` (the dbt templater calls `dbt compile` which connects to BQ)
- `python -m ingestion.api_football.main` (also needs `API_FOOTBALL_API_KEY`)

### Gotchas

- **`GOOGLE_APPLICATION_CREDENTIALS` injected as JSON content, not a file path.** The GCP SDK expects a file path, but the Cursor secret is injected as raw JSON. You must write it to disk and re-export the env var as the file path (see "GCP credential setup" above).
- **dbt profiles.yml must use `method: service-account`** in Cloud Agent VMs (no browser for OAuth). The update script copies the example profile which uses `method: oauth` — override `~/.dbt/profiles.yml` on first use.
- **SQLFluff requires BigQuery auth.** The `.sqlfluff` config uses `templater = dbt`, which invokes `dbt compile` internally. Without GCP credentials, linting fails.
- **Run SQLFluff from `dbt_project/`**, not the repo root, so the dbt templater picks up `.sqlfluff`.
- **`dbt_project.yml` warning about unused snapshot config** is benign — it fires because no snapshot models are currently defined under that path.
- **Python 3.12** works with the current dependency set despite the README mentioning 3.11.
- **`core.hooksPath`** may be set in the git config, blocking `pre-commit install`. Run `git config --unset-all core.hooksPath` first if you see "Cowardly refusing to install hooks."
- **`dbt build` takes ~7 minutes** for the full project (153 views, 29 tables, 677 tests, 3 seeds).
