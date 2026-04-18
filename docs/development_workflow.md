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
