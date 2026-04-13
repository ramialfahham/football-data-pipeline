# Development Workflow

This workflow is the default way to continue development in this repository.
It is designed for quality, reproducibility, and safe public-repo hygiene.

## 1) Start of Session

```powershell
git checkout main
git pull origin main
git checkout -b feat/<short-topic>
```

Branch naming:

- `feat/<topic>`
- `fix/<topic>`
- `docs/<topic>`
- `refactor/<topic>`

## 2) Build in Small Slices

Keep each change focused to one concern:

- ingestion changes
- staging/base/core model changes
- docs/standards updates

Avoid mixing unrelated changes in the same commit.

## 3) Layer Contract Checks

Before committing, confirm:

- `1_staging`: source-near cleanup only, no cross-source unions.
- `2_base`: canonicalization/unions/entity resolution.
- `3_core`: stable dimensional/fact entities.
- `4_intermediate`: heavy transforms/features.
- `5_marts`: consumer-facing outputs.

## 4) Required Validation Commands

Run from repo root with the root venv active:

```powershell
dbt deps --project-dir .\dbt_project
dbt parse --project-dir .\dbt_project
dbt build --project-dir .\dbt_project --selector staging
dbt build --project-dir .\dbt_project --selector base
```

If `dbt` is not on your PATH after `pip install -r requirements.txt`, invoke the CLI from your Python **Scripts** directory (Windows example: `%LocalAppData%\Programs\Python\Python311\Scripts\dbt.exe`, or run `python -c "import sysconfig; print(sysconfig.get_path('scripts'))"` to print the folder).

If ingestion code changed, also run syntax checks:

```powershell
Get-ChildItem ingestion\api_football\ -Recurse -Filter *.py | ForEach-Object { python -m py_compile $_.FullName }
```

## 5) Data Quality and Documentation Gate

For every new/changed model:

- model has a `description`
- business-relevant columns have `description`
- required tests exist (`not_null`, `unique`, `accepted_values`, etc.)
- definition confidence is tracked (`verified` vs `inferred`) where relevant

## 6) Secret Safety Gate (Public Repo)

Never commit:

- `.env` files
- API keys or tokens
- service account JSONs
- local-only files like `dbt_project/.user.yml`

Always check:

```powershell
git status --short
```

## 7) Commit and Push

Use clear, purpose-oriented commit messages:

- `feat: ...`
- `fix: ...`
- `docs: ...`
- `refactor: ...`

Then:

```powershell
git add .
git commit -m "feat: short why-focused message"
git push -u origin <branch-name>
```

## 8) Pull Request Expectations

PR should include:

- concise summary of what changed and why
- test evidence (commands run)
- data quality impact and schema impact
- migration notes for downstream consumers if needed
