import io
import json
import os

import functions_framework
import requests
from google.cloud import bigquery
from ingestion.common.ops import init_run, write_run_log

GCP_PROJECT_ID = "football-data-pipeline-gcp"
DATASET_ID = "FOOTBALL_DATA_ORG"
BASE_URL = "https://api.football-data.org/v4"

# Competition codes aligned with your current league focus.
COMPETITIONS = ["BL1", "PL", "SA", "PD", "FL1"]


def fetch_json(path: str, token: str, params: dict | None = None) -> dict:
    headers = {"X-Auth-Token": token}
    response = requests.get(f"{BASE_URL}{path}", headers=headers, params=params, timeout=60)
    response.raise_for_status()
    return response.json()


def load_json_to_bq(client: bigquery.Client, table_name: str, payload: dict) -> None:
    table_id = f"{GCP_PROJECT_ID}.{DATASET_ID}.{table_name}"
    lines = json.dumps(payload, ensure_ascii=True) + "\n"
    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
        autodetect=True,
        write_disposition="WRITE_TRUNCATE",
    )
    job = client.load_table_from_file(io.BytesIO(lines.encode("utf-8")), table_id, job_config=job_config)
    job.result()


@functions_framework.http
def load_football_data_org(request):
    token = os.getenv("FOOTBALL_DATA_ORG_API_TOKEN")
    if not token:
        return "Missing env var FOOTBALL_DATA_ORG_API_TOKEN", 400

    client = bigquery.Client(project=GCP_PROJECT_ID)
    run_ctx = init_run("football_data_org")
    errors = []
    loaded_tables = 0
    try:
        # 1) Static competition/team metadata
        for code in COMPETITIONS:
            try:
                teams_payload = fetch_json(f"/competitions/{code}/teams", token)
                load_json_to_bq(client, f"RAW_FDORG_TEAMS_{code}", teams_payload)
                loaded_tables += 1
            except Exception as e:
                errors.append(f"teams {code}: {e}")

        # 2) Current standings snapshot
        for code in COMPETITIONS:
            try:
                standings_payload = fetch_json(f"/competitions/{code}/standings", token)
                load_json_to_bq(client, f"RAW_FDORG_STANDINGS_{code}", standings_payload)
                loaded_tables += 1
            except Exception as e:
                errors.append(f"standings {code}: {e}")

        # 3) Upcoming fixtures for focused pre-match context
        for code in COMPETITIONS:
            try:
                matches_payload = fetch_json(
                    f"/competitions/{code}/matches",
                    token,
                    params={"status": "SCHEDULED"},
                )
                load_json_to_bq(client, f"RAW_FDORG_MATCHES_SCHEDULED_{code}", matches_payload)
                loaded_tables += 1
            except Exception as e:
                errors.append(f"matches {code}: {e}")

        status = "success" if not errors else "partial_success"
        write_run_log(
            client=client,
            project_id=GCP_PROJECT_ID,
            run_ctx=run_ctx,
            status=status,
            tables_loaded=loaded_tables,
            errors_count=len(errors),
            error_sample=errors[0] if errors else "",
        )
        return f"Loaded {loaded_tables} tables from football-data.org.", 200
    except Exception as e:
        write_run_log(
            client=client,
            project_id=GCP_PROJECT_ID,
            run_ctx=run_ctx,
            status="failed",
            tables_loaded=loaded_tables,
            errors_count=len(errors) + 1,
            error_sample=str(e),
        )
        return f"Pipeline failed: {e}", 500
