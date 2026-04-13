"""
API-Football → BigQuery raw loads (D1 MVP).

Follows the API-Football response contract: check `errors`, then `paging`, then `response`
(HTTP 200 can still mean empty or partial data). Paginates endpoints that return `paging`.

Reference: https://www.api-football.com/news/post/how-to-get-started-with-api-football-the-complete-beginners-guide
"""

from __future__ import annotations

import io
import json
import os
import time
from datetime import date, datetime, timedelta

import requests
from google.cloud import bigquery
from google.cloud.exceptions import NotFound


def _load_dotenv() -> None:
    """Load repo-root `.env` into the process (optional dependency)."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    load_dotenv(os.path.join(root, ".env"))


_load_dotenv()

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


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name, "").strip()
    if raw == "":
        return default
    return int(raw)


def season_year() -> int:
    """
    Competition season = API's **start year** (e.g. 2024 for 2024/25).

    If ``API_FOOTBALL_SEASON`` is set, it wins (use this on paid plans for the real current season).

    If unset, we use ``utcnow().year - 1`` then **clamp** to
    ``[API_FOOTBALL_SEASON_MIN, API_FOOTBALL_SEASON_MAX]`` so free-tier keys
    (often limited to a band like 2022–2024) still ingest without manual env
    every year. Widen or remove the clamp by setting env bounds or an explicit season.
    """
    raw = os.getenv("API_FOOTBALL_SEASON")
    if raw is not None and raw.strip() != "":
        return int(raw.strip())
    candidate = datetime.utcnow().year - 1
    lo = _env_int("API_FOOTBALL_SEASON_MIN", 2022)
    hi = _env_int("API_FOOTBALL_SEASON_MAX", 2024)
    if lo > hi:
        raise ValueError("API_FOOTBALL_SEASON_MIN must be <= API_FOOTBALL_SEASON_MAX")
    return min(max(candidate, lo), hi)


def _default_fixture_date_range(season: int, days: int) -> tuple[str, str]:
    """
    Inclusive ``from`` / ``to`` for ``from_to`` mode when env dates are not set.

    Uses the last ``days`` days inside the API ``season`` (July 1 ``season`` through
    June 30 ``season+1``), capped by UTC **today** and by **May 31 ``season+1``** so we
    do not land in the summer break (e.g. mid–late June) where many domestic leagues
    have **no** ``league`` fixtures — which produced empty ``response`` for D1.
    """
    today = datetime.utcnow().date()
    season_start = date(season, 7, 1)
    season_end = date(season + 1, 6, 30)
    # Typical last domestic matchdays are by end of May; June is often empty for league id.
    regular_season_end = date(season + 1, 5, 31)
    end = min(today, season_end, regular_season_end)
    if end < season_start:
        end = min(season_start + timedelta(days=max(days - 1, 0)), season_end)
        start = season_start
    else:
        start = end - timedelta(days=max(days - 1, 0))
        if start < season_start:
            start = season_start
            end = min(season_end, start + timedelta(days=max(days - 1, 0)))
    return start.isoformat(), end.isoformat()


def fixtures_query_params(league_id: int, season: int) -> dict:
    """
    Paid plans can use `next`. Free tier commonly rejects `next` (plan error); default is `from_to`.
    """
    mode = os.getenv("API_FOOTBALL_FIXTURES_MODE", "from_to").strip().lower()
    base = {"league": league_id, "season": season}
    if mode in ("from_to", "range", "daterange"):
        date_from = os.getenv("API_FOOTBALL_FIXTURE_FROM")
        date_to = os.getenv("API_FOOTBALL_FIXTURE_TO")
        if date_from and date_to:
            return {**base, "from": date_from.strip(), "to": date_to.strip()}
        days = int(os.getenv("API_FOOTBALL_FIXTURE_RANGE_DAYS", "14"))
        start_s, end_s = _default_fixture_date_range(season, days)
        return {**base, "from": start_s, "to": end_s}
    if mode == "next":
        return {**base, "next": 20}
    raise ValueError(
        "API_FOOTBALL_FIXTURES_MODE must be 'from_to' (default) or 'next'"
    )


def _request_pause_seconds() -> float:
    """
    Pause after each successful HTTP response.

    When ``API_FOOTBALL_REQUEST_PAUSE_MS`` is unset, default **6600 ms** (~9 calls/min)
    to stay under common free-tier **10 requests/minute** limits. Set to ``0`` for no pause (paid / CI).
    """
    raw = os.getenv("API_FOOTBALL_REQUEST_PAUSE_MS")
    if raw is None or str(raw).strip() == "":
        return 6.6
    try:
        return max(0.0, float(str(raw).strip()) / 1000.0)
    except ValueError:
        return 6.6


def _throttle() -> None:
    delay = _request_pause_seconds()
    if delay:
        time.sleep(delay)


def _maybe_log_quota(response_headers: dict) -> None:
    if os.getenv("API_FOOTBALL_LOG_QUOTA", "").strip() not in ("1", "true", "yes"):
        return
    daily = response_headers.get("x-ratelimit-requests-remaining")
    minute = response_headers.get("X-Ratelimit-Remaining") or response_headers.get(
        "x-ratelimit-remaining"
    )
    if daily is not None or minute is not None:
        print(
            f"[api-football] quota headers: daily_remaining={daily!r} per_minute={minute!r}",
            flush=True,
        )


def _flatten_api_errors(raw) -> list[str]:
    """Normalize API `errors` field (empty list, strings, dicts, or list of mixed)."""
    if raw is None:
        return []
    if isinstance(raw, str) and raw.strip():
        return [raw.strip()]
    if isinstance(raw, dict):
        if not raw:
            return []
        parts = []
        for k, v in raw.items():
            if isinstance(v, (dict, list)):
                parts.append(f"{k}: {json.dumps(v, ensure_ascii=True)}")
            else:
                parts.append(f"{k}: {v}")
        return ["; ".join(parts)] if parts else []
    if isinstance(raw, list):
        out: list[str] = []
        for item in raw:
            if isinstance(item, str) and item.strip():
                out.append(item.strip())
            elif isinstance(item, dict):
                out.append(json.dumps(item, ensure_ascii=True))
            elif item is not None:
                out.append(str(item))
        return out
    return [str(raw)]


def append_api_errors(data: dict, context: str, sink: list[str]) -> None:
    """Record API body errors next to a pipeline step (guide: prefer body over HTTP code alone)."""
    for msg in _flatten_api_errors(data.get("errors")):
        sink.append(f"{context}: {msg}")


def fetch_json(path: str, headers: dict, params: dict | None = None) -> dict:
    """
    GET JSON from API-Football. Retries 429 / 5xx once with backoff (guide: safe single retry).
    """
    url = f"{base_url()}{path}"
    params = dict(params or {})
    for attempt in range(2):
        response = requests.get(url, headers=headers, params=params, timeout=60)
        if response.status_code == 429 and attempt == 0:
            ra = response.headers.get("Retry-After", "")
            wait = float(ra) if ra.isdigit() else 3.0
            time.sleep(wait)
            continue
        if 500 <= response.status_code < 600 and attempt == 0:
            time.sleep(1.5)
            continue
        response.raise_for_status()
        data = response.json()
        _maybe_log_quota(response.headers)
        _throttle()
        return data
    raise AssertionError("fetch_json: unreachable")


def _paging_done(data: dict, page: int) -> bool:
    paging = data.get("paging") or {}
    current = int(paging.get("current") or page)
    total = int(paging.get("total") or 1)
    return current >= total


def fetch_merged_paged(
    path: str,
    headers: dict,
    base_params: dict,
    *,
    paginate: bool = True,
    max_pages: int | None = None,
) -> dict:
    """
    Fetch API list endpoints. When ``paginate`` is True, merges all ``page=`` results (e.g. ``/players``).
    When False, sends ``base_params`` only — many endpoints (and free-tier plans) reject ``page``.
    """
    if not paginate:
        data = fetch_json(path, headers, params=dict(base_params))
        meta = {k: v for k, v in data.items() if k not in ("response", "errors", "results", "paging")}
        out = dict(meta)
        out["errors"] = _flatten_api_errors(data.get("errors"))
        merged = list(data.get("response") or [])
        out["response"] = merged
        out["results"] = len(merged)
        out["paging"] = {"current": 1, "total": 1}
        return out

    limit = max_pages if max_pages is not None else int(os.getenv("API_FOOTBALL_MAX_PAGES", "250"))
    merged: list = []
    meta: dict | None = None
    merged_errors: list[str] = []
    page = 1
    while page <= limit:
        params = dict(base_params)
        params["page"] = page
        data = fetch_json(path, headers, params=params)
        if meta is None:
            meta = {k: v for k, v in data.items() if k not in ("response", "errors", "results", "paging")}
        merged_errors.extend(_flatten_api_errors(data.get("errors")))
        merged.extend(data.get("response") or [])
        if _paging_done(data, page):
            break
        # Stop at hard page cap (e.g. free tier max page=3) without treating as an error.
        if page >= limit:
            break
        page += 1
    out = dict(meta)
    out["errors"] = merged_errors
    out["response"] = merged
    out["results"] = len(merged)
    out["paging"] = {"current": 1, "total": 1}
    return out


def team_ids_for_league(
    headers: dict,
    league_id: int,
    season: int,
    errors: list[str] | None = None,
) -> set[int]:
    """Bootstrap team IDs when fixtures return none (see API-Football /teams docs)."""
    data = fetch_merged_paged(
        "/teams",
        headers,
        {"league": league_id, "season": season},
        paginate=False,
    )
    if errors is not None:
        append_api_errors(data, f"teams league_id={league_id}", errors)
    ids: set[int] = set()
    for item in data.get("response", []):
        team = item.get("team") or {}
        tid = team.get("id")
        if tid:
            ids.add(int(tid))
    return ids


def players_response_for_team(
    headers: dict,
    team_id: int,
    season: int,
    errors: list[str] | None = None,
    *,
    error_context: str = "",
) -> list:
    """All /players pages for team+season (API paginates; free tier caps ``page`` — see env)."""
    max_page = _env_int("API_FOOTBALL_PLAYERS_MAX_PAGE", 3)
    data = fetch_merged_paged(
        "/players",
        headers,
        {"team": team_id, "season": season},
        max_pages=max_page,
    )
    if errors is not None:
        ctx = error_context or f"players team_id={team_id}"
        append_api_errors(data, ctx, errors)
    return list(data.get("response") or [])


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
    errors: list[str] = []
    tables_loaded = 0

    try:
        headers = get_headers()
        season = season_year()
        _lo = _env_int("API_FOOTBALL_SEASON_MIN", 2022)
        _hi = _env_int("API_FOOTBALL_SEASON_MAX", 2024)
        _raw = os.getenv("API_FOOTBALL_SEASON", "").strip() or "(unset → auto)"
        print(
            f"[api-football] resolved_season={season} API_FOOTBALL_SEASON={_raw!r} "
            f"auto_clamp_when_unset={_lo}-{_hi}",
            flush=True,
        )

        for league_code, league_id in LEAGUES.items():
            try:
                fixtures_next = fetch_merged_paged(
                    "/fixtures",
                    headers,
                    fixtures_query_params(league_id, season),
                    paginate=False,
                )
                append_api_errors(fixtures_next, f"fixtures {league_code}", errors)
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

                # If fixtures returned no teams (empty `next`, free-tier limits, off-season),
                # fall back to all clubs in the league via /teams.
                if not team_ids:
                    try:
                        team_ids = team_ids_for_league(headers, league_id, season, errors)
                    except Exception as e:
                        errors.append(f"teams fallback {league_code}: {e}")

                # Player pool snapshot (team squads).
                players_payload = {"league_code": league_code, "response": []}
                for team_id in sorted(team_ids):
                    try:
                        players_rows = players_response_for_team(
                            headers,
                            team_id,
                            season,
                            errors,
                            error_context=f"players {league_code} team_id={team_id}",
                        )
                        players_payload["response"].append(
                            {"team_id": team_id, "players_payload": players_rows}
                        )
                    except Exception as e:
                        errors.append(f"players {league_code} team {team_id}: {e}")
                load_json_to_bq(client, f"RAW_APIF_PLAYERS_{league_code}", players_payload)
                tables_loaded += 1

                # Lineups: typically published shortly before kickoff; empty response is normal early.
                lineups_payload = {"league_code": league_code, "response": []}
                for fixture_id in sorted(fixture_ids):
                    try:
                        lineups = fetch_json(
                            "/fixtures/lineups",
                            headers=headers,
                            params={"fixture": fixture_id},
                        )
                        append_api_errors(
                            lineups,
                            f"lineups {league_code} fixture {fixture_id}",
                            errors,
                        )
                        lineups_payload["response"].append(
                            {"fixture_id": fixture_id, "lineups": lineups.get("response", [])}
                        )
                    except Exception as e:
                        errors.append(f"lineups {league_code} fixture {fixture_id}: {e}")
                load_json_to_bq(client, f"RAW_APIF_LINEUPS_{league_code}", lineups_payload)
                tables_loaded += 1

                try:
                    injuries_payload = fetch_merged_paged(
                        "/injuries",
                        headers,
                        {"league": league_id, "season": season},
                        paginate=False,
                    )
                    append_api_errors(injuries_payload, f"injuries {league_code}", errors)
                    load_json_to_bq(client, f"RAW_APIF_INJURIES_{league_code}", injuries_payload)
                    tables_loaded += 1
                except Exception as e:
                    errors.append(f"injuries {league_code}: {e}")
            except Exception as e:
                errors.append(f"league {league_code}: {e}")

        msg = f"Loaded {tables_loaded} API-Football tables."
        if errors:
            shown = errors[:40]
            tail = "; ".join(shown)
            if len(errors) > 40:
                tail += f" … (+{len(errors) - 40} more)"
            msg += f" Notes: {tail}"
        return msg, 200
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
