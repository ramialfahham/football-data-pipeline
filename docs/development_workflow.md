# Development workflow

## Local validation

Run from the repo root with the `.venv` from `README.md` activated.

```powershell
dbt deps --project-dir .\dbt_project
```

Install the dbt packages declared in `packages.yml`.

```powershell
dbt parse --project-dir .\dbt_project
```

Syntax-check every model; does not touch BigQuery.

```powershell
dbt build --project-dir .\dbt_project --selector staging
dbt build --project-dir .\dbt_project --selector base
```

Build and test staging models, then base models, against BigQuery.

If ingestion Python changed, also compile-check it:

```powershell
Get-ChildItem ingestion\api_football\ -Recurse -Filter *.py | ForEach-Object { python -m py_compile $_.FullName }
```

Run the ingestion loader smoke test to catch import/wiring errors (for example missing merge-helper imports) before a pipeline run:

```powershell
python -m unittest tests.test_ingestion_loads_smoke
```

If `dbt` is not on PATH after `pip install -r requirements.txt`, invoke it from the Python Scripts directory (Windows example: `%LocalAppData%\Programs\Python\Python311\Scripts\dbt.exe`; `python -c "import sysconfig; print(sysconfig.get_path('scripts'))"` prints the folder).

## Secret safety (public repo)

Never commit:

- `.env` files
- API keys or tokens
- service account JSONs
- local-only files like `dbt_project/.user.yml`

`git status --short` lists every added, modified, or untracked path. Review it before every commit.

```powershell
git status --short
```

### Enforced guardrails

This repo uses two automated secret checks:

1. **Local pre-commit hook** (`.pre-commit-config.yaml`) blocks obvious secrets before commit.
2. **CI secret scan** (`.github/workflows/security-secrets.yml`) runs `gitleaks` on push/PR.

Set up local guardrails once:

```powershell
pip install pre-commit
pre-commit install
```

Run checks manually anytime:

```powershell
pre-commit run --all-files
```

If a real token/key was ever committed:

1. Rotate/revoke it immediately at the provider.
2. Replace file value with placeholder.
3. Commit the cleanup.
