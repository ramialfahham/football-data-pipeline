"""Constants, env helpers, and API provider URLs for API-Football ingestion."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any


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

@dataclass(frozen=True)
class Competition:
    league_code: str
    provider: str
    provider_league_id: int
    status: str
    name: str
    form_source: str = "league_only"
    supporting_leagues: tuple = ()
    current_season: int | None = None  # from registry; used to bound season discovery for non-split-year competitions


_ALLOWED_STATUSES = {"active", "in_progress", "planned", "backlog", "completed"}


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _competition_registry_path() -> Path:
    raw = os.getenv("API_FOOTBALL_COMPETITION_REGISTRY_PATH", "").strip()
    if raw:
        p = Path(raw)
        return p if p.is_absolute() else (_repo_root() / p)
    return _repo_root() / "docs" / "competition_registry.yml"


def _load_registry_yaml() -> dict[str, Any]:
    path = _competition_registry_path()
    if not path.exists():
        raise ValueError(
            f"Competition registry not found at {path}. "
            "Set API_FOOTBALL_COMPETITION_REGISTRY_PATH or restore docs/competition_registry.yml."
        )
    try:
        import yaml
    except ImportError as exc:
        raise ValueError(
            "PyYAML is required for competition registry parsing. "
            "Install dependencies with `pip install -r requirements.txt`."
        ) from exc
    with path.open("r", encoding="utf-8") as f:
        parsed = yaml.safe_load(f) or {}
    if not isinstance(parsed, dict):
        raise ValueError(f"Competition registry at {path} must parse to a top-level object.")
    return parsed


def _parse_competitions() -> list[Competition]:
    doc = _load_registry_yaml()
    entries = doc.get("competitions")
    if not isinstance(entries, list):
        raise ValueError("Competition registry must contain a `competitions` list.")

    out: list[Competition] = []
    seen_codes: set[str] = set()
    for idx, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise ValueError(f"Competition entry #{idx + 1} must be an object.")

        league_code = str(entry.get("league_code", "")).strip().upper()
        provider = str(entry.get("provider", "")).strip().lower()
        status = str(entry.get("status", "")).strip().lower()
        name = str(entry.get("name", "")).strip() or league_code
        provider_league_id_raw = entry.get("provider_league_id")
        competition_type = str(entry.get("competition_type", "")).strip().lower()
        form_source = str(entry.get("form_source", "")).strip().lower()
        supporting_leagues = entry.get("supporting_leagues")

        if not league_code:
            raise ValueError(f"Competition entry #{idx + 1}: missing `league_code`.")
        if league_code in seen_codes:
            raise ValueError(f"Competition registry has duplicate league_code `{league_code}`.")
        seen_codes.add(league_code)

        if provider != "api_football":
            continue

        if status not in _ALLOWED_STATUSES:
            raise ValueError(
                f"Competition `{league_code}` has invalid status `{status}`. "
                f"Allowed: {sorted(_ALLOWED_STATUSES)}"
            )
        if provider_league_id_raw is None:
            raise ValueError(
                f"Competition `{league_code}` is missing `provider_league_id`."
            )
        try:
            provider_league_id = int(provider_league_id_raw)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"Competition `{league_code}` has non-integer provider_league_id={provider_league_id_raw!r}."
            ) from exc

        parsed_supporting_leagues: tuple = ()
        if (
            competition_type == "international_tournament"
            and form_source == "supporting_leagues"
            and status in {"active", "in_progress"}
        ):
            if not isinstance(supporting_leagues, list) or not supporting_leagues:
                raise ValueError(
                    f"Competition `{league_code}` requires non-empty `supporting_leagues` "
                    "for form_source=supporting_leagues."
                )
            sl_list = []
            for idx2, sl in enumerate(supporting_leagues):
                if not isinstance(sl, dict):
                    raise ValueError(
                        f"Competition `{league_code}` supporting_leagues[{idx2}] must be an object."
                    )
                if "id" not in sl:
                    raise ValueError(
                        f"Competition `{league_code}` supporting_leagues[{idx2}] missing required `id`."
                    )
                try:
                    league_id_val = int(sl["id"])
                except (TypeError, ValueError) as exc:
                    raise ValueError(
                        f"Competition `{league_code}` supporting_leagues[{idx2}] has non-integer id={sl.get('id')!r}."
                    ) from exc
                season_val = sl.get("season")
                if season_val is not None:
                    try:
                        season_val = int(season_val)
                    except (TypeError, ValueError) as exc:
                        raise ValueError(
                            f"Competition `{league_code}` supporting_leagues[{idx2}] has non-integer season={sl.get('season')!r}."
                        ) from exc
                sl_list.append({"id": league_id_val, "season": season_val})
            parsed_supporting_leagues = tuple(sl_list)

        current_season_raw = entry.get("current_season")
        current_season: int | None = None
        if current_season_raw is not None:
            try:
                current_season = int(current_season_raw)
            except (TypeError, ValueError):
                pass

        out.append(
            Competition(
                league_code=league_code,
                provider=provider,
                provider_league_id=provider_league_id,
                status=status,
                name=name,
                form_source=form_source or "league_only",
                supporting_leagues=parsed_supporting_leagues,
                current_season=current_season,
            )
        )
    if not out:
        raise ValueError(
            "Competition registry contains no API-Football competitions with provider_league_id."
        )
    return out


def include_in_progress_competitions() -> bool:
    return _env_truthy("API_FOOTBALL_INCLUDE_IN_PROGRESS", default=False)


def selected_competitions() -> tuple[list[Competition], list[tuple[Competition, str]]]:
    selected: list[Competition] = []
    skipped: list[tuple[Competition, str]] = []
    allow_in_progress = include_in_progress_competitions()
    for comp in _parse_competitions():
        if comp.status == "active":
            selected.append(comp)
        elif comp.status == "in_progress" and allow_in_progress:
            selected.append(comp)
        elif comp.status == "in_progress":
            skipped.append(
                (
                    comp,
                    "status=in_progress and API_FOOTBALL_INCLUDE_IN_PROGRESS is not enabled",
                )
            )
        else:
            skipped.append((comp, f"status={comp.status} is excluded by policy"))
    if not selected:
        raise ValueError(
            "No competitions selected for ingestion. "
            "Review competition status values and API_FOOTBALL_INCLUDE_IN_PROGRESS."
        )
    return selected, skipped


def selected_leagues_map() -> dict[str, int]:
    comps, _ = selected_competitions()
    return {c.league_code: c.provider_league_id for c in comps}

# v1 milestone: last N API ``season`` start years **including** the active campaign (see
# ``_infer_competition_season_start_year``). Fixed N here — widen in code later if v2 needs it.
V1_SEASON_WINDOW_YEARS = 10


def raw_league_table(league_code: str, entity: str) -> str:
    """BigQuery table name (not project-qualified): ``RAW_APIF_BL1_FIXTURES_NEXT``.

    Convention: RAW_APIF_{league_code}_{entity}
    Provider first, then internal league_code, then endpoint.
    """
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


def _infer_competition_season_start_year(now: datetime | None = None) -> int:
    """Infer the current API season start year for split-year domestic leagues.

    The API uses the start calendar year as the season identifier (e.g. 2024 for
    2024/25 Bundesliga). Domestic leagues start in July, so:
    - On or after 1 July: the new season has started → return this calendar year.
    - Before 1 July: the previous season is still active → return calendar year - 1.

    This is only correct for split-year domestic leagues. For calendar-year
    competitions (WC, qualifiers), use current_season from the registry instead.
    """
    today = (now or datetime.utcnow()).date()
    if today >= date(today.year, 7, 1):
        return today.year
    return today.year - 1


def effective_season_min() -> int:
    """Lower bound: ``V1_SEASON_WINDOW_YEARS`` start years ending at the active campaign."""
    hi = _infer_competition_season_start_year()
    return hi - (V1_SEASON_WINDOW_YEARS - 1)


def effective_season_max() -> int:
    """Upper bound: active campaign API season start year."""
    return _infer_competition_season_start_year()


def _default_season_min() -> int:
    return effective_season_min()


def _default_season_max() -> int:
    return effective_season_max()


def season_year() -> int:
    """
    Competition season = API's **start year** (e.g. 2024 for 2024/25).

    If ``API_FOOTBALL_SEASON`` is set, it wins.

    If unset, we infer the **current** campaign via :func:`_infer_competition_season_start_year`
    then clamp to the v1 window ``[effective_season_min(), effective_season_max()]``
    (last ``V1_SEASON_WINDOW_YEARS`` API season start years, inclusive). Set
    ``API_FOOTBALL_SEASONS`` for an explicit list when needed.
    """
    raw = os.getenv("API_FOOTBALL_SEASON")
    if raw is not None and raw.strip() != "":
        return int(raw.strip())
    candidate = _infer_competition_season_start_year()
    lo = effective_season_min()
    hi = effective_season_max()
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
    **Full** profile = standard paid / warehouse ingestion: multi-season pull within the
    v1 window (``V1_SEASON_WINDOW_YEARS``), no request pacing unless you set it, and
    high pagination caps.
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
    d.setdefault("API_FOOTBALL_TRANSFERS_MAX_PAGE", "50")
    d.setdefault("API_FOOTBALL_PLAYERS_RESERVE_CALLS", "20")
    d.setdefault("API_FOOTBALL_FANOUT_SOFT_CAP_FIXTURES_NO_HEADER", "-1")
    d.setdefault("API_FOOTBALL_MAX_PAGES", "250")
    d.setdefault("API_FOOTBALL_FIXTURES_MAX_PAGE", "50")
    print(
        "[api-football] ingest profile=full -> unset env got paid defaults "
        f"(multi-season within v1 window last {V1_SEASON_WINDOW_YEARS} API season years, "
        "REQUEST_PAUSE_MS=0, higher page caps, fanout soft cap off). "
        "Unset API_FOOTBALL_SEASON for multi-season; set any var explicitly to override.",
        flush=True,
    )
