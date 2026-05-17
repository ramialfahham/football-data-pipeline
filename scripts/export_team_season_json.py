"""Export marts.mart_team_season_insights from BigQuery to app-ready team_season_insights.json.

Powers the per-team season retrospective page (site/team-season/). Grain: one row
per (league_code, team) for the latest season_api_year per league. Filtered to
BL1 only until the UI can switch or filter by league_code (mirroring the
matchday-insights filter).

Output format: {"teams": [...rows...]} sorted by latest_rank ascending so the
page's carousel walks the standings top-to-bottom by default.

Usage:
    python scripts/export_team_season_json.py <output_path>

Authentication: uses Application Default Credentials (set by google-github-actions/auth
in CI, or by `gcloud auth application-default login` locally).
"""
from __future__ import annotations

import json
import pathlib
import sys


GCP_PROJECT = "football-data-pipeline-gcp"
MART_TABLE = f"{GCP_PROJECT}.marts.mart_team_season_insights"

# BL1-only for now (mirrors the matchday-insights export). When the UI learns
# to switch competitions, drop this filter or pass it in as a CLI argument.
LEAGUE_FILTER = "BL1"


def _bigquery_rows_to_dicts(rows) -> list[dict]:
    return [dict(row.items()) for row in rows]


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: export_team_season_json.py <output_path>")
        return 1

    output_path = pathlib.Path(sys.argv[1])
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        from google.cloud import bigquery
    except ImportError:
        print("google-cloud-bigquery is not installed. Run: pip install -r requirements.txt")
        return 1

    client = bigquery.Client(project=GCP_PROJECT)
    query = f"""
        SELECT *
        FROM `{MART_TABLE}`
        WHERE league_code = @league_code
        ORDER BY latest_rank ASC
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("league_code", "STRING", LEAGUE_FILTER)]
    )

    print(f"Querying {MART_TABLE} for league_code={LEAGUE_FILTER} ...", flush=True)
    rows = list(client.query(query, job_config=job_config).result())
    print(f"Retrieved {len(rows)} rows.", flush=True)

    payload = {"teams": _bigquery_rows_to_dicts(rows)}
    output_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    print(f"Wrote {output_path} ({len(rows)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
