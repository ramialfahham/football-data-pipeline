"""Export marts.mart_wc_pre_tournament_insights to wc_pre_tournament_insights.json.

Powers the WC pre-tournament team view (Phase C). Grain: one row per WC 2026
participant (team_sk). The UI must show a metric value only when the matching
is_*_complete column is true; otherwise show "—" or a thin-data label.

Output shape:
    {
      "league_code": "WC",
      "season_api_year": <int from mart>,
      "teams": [ ...rows sorted by team_name... ]
    }

Usage:
    python scripts/export_wc_pre_tournament_json.py <output_path>

Authentication: Application Default Credentials (CI WIF or gcloud ADC locally).
"""
from __future__ import annotations

import json
import pathlib
import sys
from datetime import datetime, timezone


GCP_PROJECT = "football-data-pipeline-gcp"
MART_TABLE = f"{GCP_PROJECT}.marts.mart_wc_pre_tournament_insights"
LEAGUE_CODE = "WC"


def _bigquery_rows_to_dicts(rows) -> list[dict]:
    return [dict(row.items()) for row in rows]


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: export_wc_pre_tournament_json.py <output_path>")
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
        ORDER BY team_name ASC
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("league_code", "STRING", LEAGUE_CODE)]
    )

    print(f"Querying {MART_TABLE} for league_code={LEAGUE_CODE} ...", flush=True)
    rows = list(client.query(query, job_config=job_config).result())
    print(f"Retrieved {len(rows)} rows.", flush=True)

    season_api_year = None
    if rows:
        season_api_year = rows[0].get("season_api_year")

    payload = {
        "league_code": LEAGUE_CODE,
        "season_api_year": season_api_year,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "teams": _bigquery_rows_to_dicts(rows),
    }
    output_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    print(f"Wrote {output_path} ({len(rows)} teams)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
