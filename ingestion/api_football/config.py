"""Constants, env helpers, and API provider URLs for API-Football ingestion."""

from __future__ import annotations

import os
from datetime import date, datetime


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
# BigQuery dataset for 1:1 loads (medallion "raw" layer). Override to match dbt `sources` schema.
DATASET_ID = (os.getenv("API_FOOTBALL_BIGQUERY_DATASET", "raw").strip() or "raw")

APISPORTS_BASE = "https://v3.football.api-sports.io"
RAPIDAPI_BASE = "https://api-football-v1.p.rapidapi.com/v3"

# API-Football league IDs — MVP: German Bundesliga only.
LEAGUES = {
    "D1": 78,  # Bundesliga
}


def raw_league_table(league_code: str, entity: str) -> str:
    """
    League-first BigQuery **table name** (not project-qualified): ``RAW_D1_APIF_FIXTURES_NEXT``.

    Puts competition code before the vendor segment so multiple leagues sort and filter cleanly.
    """
    return f"RAW_{league_code}_APIF_{entity}"


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
        raise ValueError(
            "Missing API_FOOTBALL_API_KEY. Add it once to a repo-root `.env` "
            "(copy `.env.example` to `.env`) and ensure `python-dotenv` is installed "
            "(`pip install -r requirements.txt` at repo root, or "
            "`pip install -r ingestion/api_football/requirements.txt`)."
        )
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


def _infer_competition_season_start_year(now: datetime | None = None) -> int:
    """
    API ``season`` = competition **start calendar year** (e.g. 2025 for 2025/26).

    Domestic leagues are modelled from **1 July**: on/after that date the active
    campaign is ``calendar_year / (calendar_year+1)`` → API season = that year;
    before July it is still the previous campaign → ``calendar_year - 1``.
    """
    today = (now or datetime.utcnow()).date()
    if today >= date(today.year, 7, 1):
        return today.year
    return today.year - 1


def _default_season_min() -> int:
    """Lower bound when auto-picking or filtering discovered seasons (override via env)."""
    return _env_int("API_FOOTBALL_SEASON_MIN", 1990)


def _default_season_max() -> int:
    """Upper bound defaults to the current calendar year so the active season is never clamped away."""
    return _env_int("API_FOOTBALL_SEASON_MAX", datetime.utcnow().year)


def season_year() -> int:
    """
    Competition season = API's **start year** (e.g. 2024 for 2024/25).

    If ``API_FOOTBALL_SEASON`` is set, it wins.

    If unset, we infer the **current** campaign via :func:`_infer_competition_season_start_year`
    then clamp to ``[API_FOOTBALL_SEASON_MIN, API_FOOTBALL_SEASON_MAX]`` (defaults
    ``1990`` .. ``current calendar year``). Narrow the band on strict keys, or set
    ``API_FOOTBALL_ALL_SEASONS`` / ``API_FOOTBALL_SEASONS`` for multi-season loads.
    """
    raw = os.getenv("API_FOOTBALL_SEASON")
    if raw is not None and raw.strip() != "":
        return int(raw.strip())
    candidate = _infer_competition_season_start_year()
    lo = _default_season_min()
    hi = _default_season_max()
    if lo > hi:
        raise ValueError("API_FOOTBALL_SEASON_MIN must be <= API_FOOTBALL_SEASON_MAX")
    return min(max(candidate, lo), hi)


def _env_truthy(name: str, default: bool = False) -> bool:
    v = os.getenv(name, "").strip().lower()
    if v == "":
        return default
    return v in ("1", "true", "yes", "on")


def _ingest_profile_name() -> str:
    raw = os.getenv("API_FOOTBALL_INGEST_PROFILE", "").strip().lower()
    if raw:
        return raw
    if _env_truthy("API_FOOTBALL_PAID_FULL_LOAD"):
        return "full"
    # Default mirrors a paid / warehouse run: all API-listed seasons + generous caps.
    # Opt into free-tier pacing with API_FOOTBALL_INGEST_PROFILE=default (or economy).
    return "full"


def _apply_ingest_profile_defaults() -> None:
    """
    **Full** profile = standard paid / warehouse ingestion: all seasons the API exposes
    for the league, no request pacing unless you set it, and high pagination caps.
    Only uses ``os.environ.setdefault`` so anything you export explicitly still wins.

    **Economy** profile (``INGEST_PROFILE=default`` / ``economy`` / ``free``): no bundled
    defaults here—single inferred season and conservative request pacing from other
    env defaults.

    When ``API_FOOTBALL_INGEST_PROFILE`` is unset, :func:`_ingest_profile_name` returns
    ``full`` so this function normally runs.
    """
    prof = _ingest_profile_name()
    if prof not in ("full", "paid", "complete"):
        if prof not in ("", "default", "economy", "free"):
            print(
                f"[api-football] unknown API_FOOTBALL_INGEST_PROFILE={prof!r} "
                f"(use full|default|economy); treating as economy (no bundled paid defaults).",
                flush=True,
            )
        return

    d = os.environ
    d.setdefault("API_FOOTBALL_ALL_SEASONS", "1")
    d.setdefault("API_FOOTBALL_REQUEST_PAUSE_MS", "0")
    d.setdefault("API_FOOTBALL_PLAYERS_MAX_PAGE", "50")
    d.setdefault("API_FOOTBALL_ODDS_MAX_PAGE", "30")
    d.setdefault("API_FOOTBALL_TRANSFERS_MAX_PAGE", "50")
    d.setdefault("API_FOOTBALL_FANOUT_SOFT_CAP_FIXTURES_NO_HEADER", "-1")
    d.setdefault("API_FOOTBALL_MAX_PAGES", "250")
    d.setdefault("API_FOOTBALL_FIXTURES_MAX_PAGE", "50")
    print(
        "[api-football] ingest profile=full -> unset env got paid defaults "
        "(catalog multi-season, REQUEST_PAUSE_MS=0, higher page caps, fanout soft cap off). "
        "Unset API_FOOTBALL_SEASON for multi-season; set any var explicitly to override.",
        flush=True,
    )
