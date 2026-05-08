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
    form_source: str = "league_only"
    supporting_leagues: tuple = ()
    current_season: int | None = None  # from registry; used to bound season discovery for non-split-year competitions
    history_seasons: int | None = None  # CPO-approved backfill window (number of season start years)


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

        history_seasons_raw = entry.get("history_seasons")
        history_seasons: int | None = None
        if history_seasons_raw is not None:
            try:
                hs = int(history_seasons_raw)
                if hs >= 1:
                    history_seasons = hs
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
                history_seasons=history_seasons,
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
