import io
import json
import os
from datetime import datetime, timedelta

import requests
from google.cloud import bigquery
from google.cloud.exceptions import NotFound

GCP_PROJECT_ID = "football-data-pipeline-gcp"
DATASET_ID = "API_FOOTBALL"

APISPORTS_BASE = "https://v3.football.api-sports.io"
RAPIDAPI_BASE = "https://api-football-v1.p.rapidapi.com/v3"

# API-Football league IDs — MVP: German Bundesliga only.
LEAGUES = {
    "D1": 78,  # Bundesliga
}


def _provider() -> str:
    return os.getenv("API_FOOTBALL_PROVIDER", "apisports").strip().lower()


def base_url() -> str:
    p = _provider()
    if p in ("rapidapi", "rapid"):
        return RAPIDAPI_BASE
    if p in ("apisports", "api_sports", "direct", ""):
        return APISPORTS_BASE
    raise ValueError(
        "API_FOOTBALL_PROVIDER must be 'apisports' (default) or 'rapidapi'"
    )


def get_headers() -> dict:
    api_key = os.getenv("API_FOOTBALL_API_KEY")
    if not api_key:
        raise ValueError("Missing env var API_FOOTBALL_API_KEY")
    if _provider() in ("rapidapi", "rapid"):
        return {
            "x-rapidapi-key": api_key,
            "x-rapidapi-host": "api-football-v1.p.rapidapi.com",
        }
    return {"x-apisports-key": api_key}


def season_year() -> int:
    raw = os.getenv("API_FOOTBALL_SEASON")
    if raw is not None and raw.strip() != "":
        return int(raw.strip())
    # Competition "season" is the starting calendar year (e.g. 2025 for 2025/26).
    return datetime.utcnow().year - 1


def fixtures_query_params(league_id: int, season: int) -> dict:
    """
    Paid plans typically support `next`. Free tier often rejects `next` and may restrict `season`;
    use from_to with explicit dates (see env vars below).
    """
    mode = os.getenv("API_FOOTBALL_FIXTURES_MODE", "next").strip().lower()
    base = {"league": league_id, "season": season}
    if mode in ("from_to", "range", "daterange"):
        date_from = os.getenv("API_FOOTBALL_FIXTURE_FROM")
        date_to = os.getenv("API_FOOTBALL_FIXTURE_TO")
        if date_from and date_to:
            return {**base, "from": date_from.strip(), "to": date_to.strip()}
        end = datetime.utcnow().date()
        days = int(os.getenv("API_FOOTBALL_FIXTURE_RANGE_DAYS", "14"))
        start = end - timedelta(days=days)
        return {
            **base,
            "from": start.isoformat(),
            "to": end.isoformat(),
        }
    if mode == "next":
        return {**base, "next": 20}
    raise ValueError(
        "API_FOOTBALL_FIXTURES_MODE must be 'next' (default) or 'from_to'"
    )


def fetch_json(path: str, headers: dict, params: dict | None = None) -> dict:
    response = requests.get(f"{base_url()}{path}", headers=headers, params=params, timeout=60)
    response.raise_for_status()
    return response.json()


def _api_football_dataset_location() -> str:
    """Must match dbt `location` in profiles.yml (default EU)."""
    return os.getenv("API_FOOTBALL_DATASET_LOCATION", "EU").strip() or "EU"


def ensure_api_football_dataset(client: bigquery.Client) -> None:
    ref = f"{GCP_PROJECT_ID}.{DATASET_ID}"
    want_loc = _api_football_dataset_location()
    try:
        existing = client.get_dataset(ref)
        got = (existing.location or "").upper()
        if got and got != want_loc.upper():
            raise RuntimeError(
                f"BigQuery dataset {ref} exists in location {existing.location!r} but "
                f"API_FOOTBALL_DATASET_LOCATION / dbt expect {want_loc!r}. "
                f"Delete dataset {DATASET_ID} in the console (or pick one region everywhere), then re-run."
            )
        return
    except NotFound:
        pass
    ds = bigquery.Dataset(ref)
    ds.location = want_loc
    client.create_dataset(ds, exists_ok=True)


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


def _load_api_football(request):
    client = bigquery.Client(project=GCP_PROJECT_ID)
    ensure_api_football_dataset(client)
    errors = []
    tables_loaded = 0

    try:
        headers = get_headers()
        season = season_year()

        for league_code, league_id in LEAGUES.items():
            try:
                fixtures_next = fetch_json(
                    "/fixtures",
                    headers=headers,
                    params=fixtures_query_params(league_id, season),
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
                            params={"team": team_id, "season": season},
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
                        params={"league": league_id, "season": season},
                    )
                    load_json_to_bq(client, f"RAW_APIF_INJURIES_{league_code}", injuries_payload)
                    tables_loaded += 1
                except Exception as e:
                    errors.append(f"injuries {league_code}: {e}")
            except Exception as e:
                errors.append(f"league {league_code}: {e}")

        return f"Loaded {tables_loaded} API-Football tables.", 200
    except Exception as e:
        return f"Pipeline failed: {e}", 500


try:
    import functions_framework

    load_api_football = functions_framework.http(_load_api_football)
except ImportError:
    load_api_football = _load_api_football


if __name__ == "__main__":
    # Local / CI: load D1 raw tables into BigQuery without Cloud Run.
    # From repo root: set PYTHONPATH=. and API_FOOTBALL_API_KEY, then:
    #   python -m ingestion.api_football.main
    class _Request:
        pass

    body, status = load_api_football(_Request())
    print(body, flush=True)
    raise SystemExit(0 if status == 200 else 1)
