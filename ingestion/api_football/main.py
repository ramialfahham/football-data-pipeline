import io
import json
import os
from datetime import datetime

import functions_framework
import requests
from google.cloud import bigquery

from ingestion.common.ops import init_run, write_run_log

GCP_PROJECT_ID = "football-data-pipeline-gcp"
DATASET_ID = "API_FOOTBALL"
BASE_URL = "https://api-football-v1.p.rapidapi.com/v3"

# API-Football league IDs (top tiers aligned with your current scope).
LEAGUES = {
    "E0": 39,    # Premier League
    "D1": 78,    # Bundesliga
    "I1": 135,   # Serie A
    "SP1": 140,  # La Liga
    "F1": 61,    # Ligue 1
}


def get_headers() -> dict:
    api_key = os.getenv("API_FOOTBALL_API_KEY")
    if not api_key:
        raise ValueError("Missing env var API_FOOTBALL_API_KEY")
    return {
        "x-rapidapi-key": api_key,
        "x-rapidapi-host": "api-football-v1.p.rapidapi.com",
    }


def fetch_json(path: str, headers: dict, params: dict | None = None) -> dict:
    response = requests.get(f"{BASE_URL}{path}", headers=headers, params=params, timeout=60)
    response.raise_for_status()
    return response.json()


def load_json_to_bq(client: bigquery.Client, table_name: str, payload: dict) -> None:
    table_id = f"{GCP_PROJECT_ID}.{DATASET_ID}.{table_name}"
    line = json.dumps(payload, ensure_ascii=True) + "\n"
    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
        autodetect=True,
        write_disposition="WRITE_TRUNCATE",
    )
    job = client.load_table_from_file(io.BytesIO(line.encode("utf-8")), table_id, job_config=job_config)
    job.result()


@functions_framework.http
def load_api_football(request):
    client = bigquery.Client(project=GCP_PROJECT_ID)
    run_ctx = init_run("api_football")
    errors = []
    tables_loaded = 0

    try:
        headers = get_headers()
        current_year = datetime.utcnow().year

        for league_code, league_id in LEAGUES.items():
            try:
                fixtures_next = fetch_json(
                    "/fixtures",
                    headers=headers,
                    params={"league": league_id, "season": current_year, "next": 20},
                )
                load_json_to_bq(client, f"RAW_APIF_FIXTURES_NEXT_{league_code}", fixtures_next)
                tables_loaded += 1

                team_ids = set()
                fixture_ids = set()
                for item in fixtures_next.get("response", []):
                    fixture = item.get("fixture", {})
                    teams = item.get("teams", {})
                    home = teams.get("home", {})
                    away = teams.get("away", {})
                    if fixture.get("id"):
                        fixture_ids.add(fixture["id"])
                    if home.get("id"):
                        team_ids.add(home["id"])
                    if away.get("id"):
                        team_ids.add(away["id"])

                # Player pool snapshot (team squads) for near-term relevant teams.
                players_payload = {"league_code": league_code, "response": []}
                for team_id in sorted(team_ids):
                    try:
                        team_players = fetch_json(
                            "/players",
                            headers=headers,
                            params={"team": team_id, "season": current_year},
                        )
                        players_payload["response"].append(
                            {"team_id": team_id, "players_payload": team_players.get("response", [])}
                        )
                    except Exception as e:
                        errors.append(f"players {league_code} team {team_id}: {e}")
                load_json_to_bq(client, f"RAW_APIF_PLAYERS_{league_code}", players_payload)
                tables_loaded += 1

                # Lineups for upcoming fixtures (fan-critical pre-match context).
                lineups_payload = {"league_code": league_code, "response": []}
                for fixture_id in sorted(fixture_ids):
                    try:
                        lineups = fetch_json("/fixtures/lineups", headers=headers, params={"fixture": fixture_id})
                        lineups_payload["response"].append(
                            {"fixture_id": fixture_id, "lineups": lineups.get("response", [])}
                        )
                    except Exception as e:
                        errors.append(f"lineups {league_code} fixture {fixture_id}: {e}")
                load_json_to_bq(client, f"RAW_APIF_LINEUPS_{league_code}", lineups_payload)
                tables_loaded += 1

                # Injuries by league/season.
                try:
                    injuries_payload = fetch_json(
                        "/injuries",
                        headers=headers,
                        params={"league": league_id, "season": current_year},
                    )
                    load_json_to_bq(client, f"RAW_APIF_INJURIES_{league_code}", injuries_payload)
                    tables_loaded += 1
                except Exception as e:
                    errors.append(f"injuries {league_code}: {e}")
            except Exception as e:
                errors.append(f"league {league_code}: {e}")

        status = "success" if not errors else "partial_success"
        write_run_log(
            client=client,
            project_id=GCP_PROJECT_ID,
            run_ctx=run_ctx,
            status=status,
            tables_loaded=tables_loaded,
            errors_count=len(errors),
            error_sample=errors[0] if errors else "",
        )
        return f"Loaded {tables_loaded} API-Football tables.", 200
    except Exception as e:
        write_run_log(
            client=client,
            project_id=GCP_PROJECT_ID,
            run_ctx=run_ctx,
            status="failed",
            tables_loaded=tables_loaded,
            errors_count=len(errors) + 1,
            error_sample=str(e),
        )
        return f"Pipeline failed: {e}", 500
