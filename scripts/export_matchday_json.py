"""Export mart_matchday_insights from BigQuery to app-ready matchday_insights.json.

Replaces the dbt show --limit N hack. Reads the already-materialised mart table
directly — no row cap, no CLI output parsing, no re-running the query through dbt.

Output format: {"show": [...rows...]} — matches the shape the UI expects.

Usage:
    python scripts/export_matchday_json.py <output_path>

Authentication: uses Application Default Credentials (set by google-github-actions/auth
in CI, or by `gcloud auth application-default login` locally).
"""
from __future__ import annotations

import json
import pathlib
import sys


GCP_PROJECT = "football-data-pipeline-gcp"
MART_TABLE = f"{GCP_PROJECT}.marts.mart_matchday_insights"


def _bigquery_rows_to_dicts(rows) -> list[dict]:
    return [dict(row.items()) for row in rows]


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: export_matchday_json.py <output_path>")
        return 1

    output_path = pathlib.Path(sys.argv[1])
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        from google.cloud import bigquery
    except ImportError:
        print("google-cloud-bigquery is not installed. Run: pip install -r requirements.txt")
        return 1

    client = bigquery.Client(project=GCP_PROJECT)
    query = f"SELECT * FROM `{MART_TABLE}`"

    print(f"Querying {MART_TABLE} ...", flush=True)
    rows = list(client.query(query).result())
    print(f"Retrieved {len(rows)} rows.", flush=True)

    payload = {"show": _bigquery_rows_to_dicts(rows)}
    output_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    print(f"Wrote {output_path} ({len(rows)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
