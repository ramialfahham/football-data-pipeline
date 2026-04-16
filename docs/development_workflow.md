# Development workflow

## Required validation commands

Run from repo root with the **`.venv`** from `README.md` activated:

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

## Secret safety (public repo)

Never commit:

- `.env` files
- API keys or tokens
- service account JSONs
- local-only files like `dbt_project/.user.yml`

Before committing, review:

```powershell
git status --short
```
