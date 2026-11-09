"""Global constants, env var helpers, ingest profile, and API provider configuration."""

from __future__ import annotations

import os


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

# Season years ingested, including the active one, when a competition sets no ``history_seasons``.
DEFAULT_SEASON_WINDOW_YEARS = 10


def raw_table(entity: str) -> str:
    """Unqualified shared table name ``RAW_APIF_{entity}``; rows carry a league_code column."""
    return f"RAW_APIF_{entity}"


def raw_league_table(league_code: str, entity: str) -> str:
    """Per-competition table name ``RAW_APIF_{LC}_{entity}``, only for pipeline-state tables."""
    return f"RAW_APIF_{league_code}_{entity}"



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
    # Free-tier pacing is opt-in via API_FOOTBALL_INGEST_PROFILE=default (or economy).
    return "full"


def _apply_ingest_profile_defaults() -> None:
    """Set paid-profile env defaults for the full profile; explicitly exported vars still win.

    The 250 ms pause protects the provider's per-minute limit, and defaults here so nothing
    inherits zero pacing by omission.
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
    d.setdefault("API_FOOTBALL_REQUEST_PAUSE_MS", "250")
    d.setdefault("API_FOOTBALL_PLAYERS_MAX_PAGE", "50")
    d.setdefault("API_FOOTBALL_PLAYERS_RESERVE_CALLS", "20")
    d.setdefault("API_FOOTBALL_FANOUT_SOFT_CAP_FIXTURES_NO_HEADER", "-1")
    d.setdefault("API_FOOTBALL_MAX_PAGES", "250")
    d.setdefault("API_FOOTBALL_FIXTURES_MAX_PAGE", "50")
    print(
        "[api-football] ingest profile=full -> unset env got paid defaults "
        f"(multi-season within the default window last {DEFAULT_SEASON_WINDOW_YEARS} API season years, "
        "REQUEST_PAUSE_MS=250, higher page caps, fanout soft cap off). "
        "Unset API_FOOTBALL_SEASON for multi-season; set any var explicitly to override.",
        flush=True,
    )
