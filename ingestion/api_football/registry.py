"""Competition registry: parses competition_registry.yml → Competition objects.

Authoritative source for which competitions are active and how to ingest them.
selected_competitions() is the pipeline entry point for deciding what to ingest.

The registry YAML lives at docs/competition_registry.yml (overridable via
API_FOOTBALL_COMPETITION_REGISTRY_PATH). Adding a new competition requires only
a registry entry — no code changes.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .settings import _env_truthy


@dataclass(frozen=True)
class Competition:
    league_code: str
    provider: str
    provider_league_id: int
    status: str
    name: str
    season_type: str = (
        "split_year"  # split_year | calendar_year — drives season hi/lo in ingestion
    )
    current_season: int | None = (
        None  # from registry; used to bound season discovery for non-split-year competitions
    )
    history_seasons: int | None = (
        None  # CPO-approved backfill window (number of season start years)
    )
    # hard: incomplete fanout fails the run; soft: report only
    ingest_completeness_gate: str = "soft"
    # CPO-controlled: False = skip ingestion entirely without changing status
    ingest_active: bool = True


_ALLOWED_STATUSES = {"active", "in_progress", "planned", "backlog", "completed"}
_COMPLETENESS_GATES = frozenset({"hard", "soft"})


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
        raise ValueError(
            f"Competition registry at {path} must parse to a top-level object."
        )
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

        if not league_code:
            raise ValueError(f"Competition entry #{idx + 1}: missing `league_code`.")
        if league_code in seen_codes:
            raise ValueError(
                f"Competition registry has duplicate league_code `{league_code}`."
            )
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

        season_type = (
            str(entry.get("season_type", "split_year")).strip().lower() or "split_year"
        )
        if season_type not in ("split_year", "calendar_year"):
            raise ValueError(
                f"Competition `{league_code}` has invalid season_type={season_type!r}. "
                "Allowed: split_year, calendar_year."
            )

        current_season_raw = entry.get("current_season")
        current_season: int | None = None
        if current_season_raw is not None:
            try:
                current_season = int(current_season_raw)
            except (TypeError, ValueError):
                pass

        history_seasons_raw = entry.get("history_seasons")
        history_seasons: int | None = None
        if history_seasons_raw is not None:
            try:
                hs = int(history_seasons_raw)
                if hs >= 1:
                    history_seasons = hs
            except (TypeError, ValueError):
                pass

        ingest_active_raw = entry.get("ingest_active")
        if ingest_active_raw is None:
            ingest_active = True  # default for backward compat; CI enforces presence
        else:
            ingest_active = bool(ingest_active_raw)

        gate_raw = str(entry.get("ingest_completeness_gate", "")).strip().lower()
        if gate_raw:
            if gate_raw not in _COMPLETENESS_GATES:
                raise ValueError(
                    f"Competition `{league_code}` has invalid ingest_completeness_gate="
                    f"{gate_raw!r}. Allowed: hard, soft."
                )
            ingest_completeness_gate = gate_raw
        elif status == "active":
            ingest_completeness_gate = "hard"
        else:
            ingest_completeness_gate = "soft"

        out.append(
            Competition(
                league_code=league_code,
                provider=provider,
                provider_league_id=provider_league_id,
                status=status,
                name=name,
                season_type=season_type,
                current_season=current_season,
                history_seasons=history_seasons,
                ingest_completeness_gate=ingest_completeness_gate,
                ingest_active=ingest_active,
            )
        )
    if not out:
        raise ValueError(
            "Competition registry contains no API-Football competitions with provider_league_id."
        )
    return out


def include_in_progress_competitions() -> bool:
    return _env_truthy("API_FOOTBALL_INCLUDE_IN_PROGRESS", default=False)


def _league_codes_filter() -> frozenset[str] | None:
    """Optional comma-separated allowlist (e.g. ``PL,PD,BL2`` for CI bootstrap)."""
    raw = os.getenv("API_FOOTBALL_LEAGUE_CODES", "").strip()
    if not raw:
        return None
    codes = frozenset(part.strip().upper() for part in raw.split(",") if part.strip())
    if not codes:
        raise ValueError(
            "API_FOOTBALL_LEAGUE_CODES is set but contains no league codes."
        )
    return codes


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
    active_selected: list[Competition] = []
    for comp in selected:
        if not comp.ingest_active:
            skipped.append((comp, "ingest_active=false"))
        else:
            active_selected.append(comp)
    selected = active_selected

    codes_filter = _league_codes_filter()
    if codes_filter is not None:
        kept: list[Competition] = []
        for comp in selected:
            if comp.league_code in codes_filter:
                kept.append(comp)
            else:
                skipped.append(
                    (
                        comp,
                        f"excluded by API_FOOTBALL_LEAGUE_CODES allowlist ({sorted(codes_filter)})",
                    )
                )
        selected = kept
    if not selected:
        raise ValueError(
            "No competitions selected for ingestion. "
            "Review competition status values, API_FOOTBALL_INCLUDE_IN_PROGRESS, "
            "and API_FOOTBALL_LEAGUE_CODES."
        )
    return selected, skipped
