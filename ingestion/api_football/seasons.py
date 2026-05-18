"""Season discovery, fixture query params, and merged API envelope helpers.

The API uses the competition start calendar year as its 'season' identifier
(e.g. 2024 = the 2024/25 Bundesliga season). This module handles three concerns:

1. Season discovery — which API season years to ingest for a given competition.
   Domestic leagues use a rolling 10-year window; international tournaments use
   current_season from the competition registry to avoid pulling irrelevant prior editions.

2. Fixture query params — how to ask the API for fixtures (full season vs. date window).

3. Envelope helpers — utilities for merging multi-season API responses into a
   single payload before writing to BigQuery.
"""

from __future__ import annotations

import os
from datetime import date, datetime, timedelta

from .settings import _env_truthy, _ingest_profile_name
from .season_inference import effective_season_max, effective_season_min, season_year
from .quota import append_api_errors, _flatten_api_errors
from .http_client import fetch_json

# Reject garbage years from odd API payloads (e.g. malformed JSON) before band filtering.
_API_SEASON_YEAR_MIN = 1900
_API_SEASON_YEAR_MAX = 2100


def _coerce_api_season_year(raw, *, context: str, errors: list[str] | None) -> int | None:
    try:
        y = int(raw)
    except (TypeError, ValueError):
        if errors is not None:
            errors.append(f"{context}: skipped non-integer season year {raw!r}")
        return None
    if _API_SEASON_YEAR_MIN <= y <= _API_SEASON_YEAR_MAX:
        return y
    if errors is not None:
        errors.append(
            f"{context}: dropped season year {y} (outside {_API_SEASON_YEAR_MIN}-{_API_SEASON_YEAR_MAX})"
        )
    return None


def _season_years_from_leagues_catalog(envelope: dict, errors: list[str] | None) -> list[int]:
    """Sorted unique API season years from a ``GET /leagues?id=`` style envelope."""
    out: set[int] = set()
    for league_entry in envelope.get("response") or []:
        for s in league_entry.get("seasons") or []:
            y = s.get("year")
            if y is None:
                continue
            yi = _coerce_api_season_year(y, context="leagues/catalog season.year", errors=errors)
            if yi is not None:
                out.add(yi)
    return sorted(out)


def _season_years_from_leagues_seasons_endpoint(
    headers: dict, league_id: int, errors: list[str]
) -> list[int]:
    """
    Fallback: ``GET /leagues/seasons`` for this league (API-Sports v3).

    Used when ``/leagues?id=`` returns a **single** season row (common with some keys
    or older responses) so multi-season ingestion still expands.
    """
    out: set[int] = set()
    try:
        data = fetch_json("/leagues/seasons", headers, params={"league": league_id})
        append_api_errors(data, f"leagues/seasons league_id={league_id}", errors)
        for row in data.get("response") or []:
            if isinstance(row, dict):
                y = row.get("year")
                if y is not None:
                    yi = _coerce_api_season_year(
                        y, context="leagues/seasons year", errors=errors
                    )
                    if yi is not None:
                        out.add(yi)
            elif type(row) is int:
                yi = _coerce_api_season_year(row, context="leagues/seasons int", errors=errors)
                if yi is not None:
                    out.add(yi)
            elif type(row) is float and row == int(row):
                yi = _coerce_api_season_year(
                    int(row), context="leagues/seasons float", errors=errors
                )
                if yi is not None:
                    out.add(yi)
            elif isinstance(row, str) and row.strip().isdigit():
                yi = _coerce_api_season_year(
                    row.strip(), context="leagues/seasons str", errors=errors
                )
                if yi is not None:
                    out.add(yi)
    except Exception as e:
        errors.append(f"leagues/seasons league_id={league_id}: {e}")
    return sorted(out)


def _api_current_season_year(league_catalog: dict) -> int | None:
    """Season year flagged ``current`` in the /leagues catalog (API source of truth)."""
    for item in (league_catalog.get("response") or []):
        for season in (item.get("seasons") or []):
            if not season.get("current"):
                continue
            try:
                return int(season["year"])
            except (TypeError, ValueError, KeyError):
                continue
    return None


def _default_profile_max_band_seasons() -> int:
    """Max seasons ingested per run on economy/default profile (form = current + prior)."""
    raw = os.getenv("API_FOOTBALL_DEFAULT_PROFILE_MAX_SEASONS", "3").strip()
    try:
        return max(1, int(raw))
    except ValueError:
        return 3


def _resolve_current_season_year(
    *,
    season_type: str,
    registry_current: int | None,
    league_catalog: dict,
) -> int:
    """Pick the active API season year.

    Order (no hard-coded league years):
    1. API /leagues catalog season with ``current: true``
    2. Type-specific inference (split-year July rule or calendar-year today)
    3. Registry ``current_season`` — optional manual override only
    """
    api_current = _api_current_season_year(league_catalog)
    if api_current is not None:
        return api_current
    if season_type == "calendar_year":
        if registry_current is not None:
            return registry_current
        return date.today().year
    inferred = season_year()
    if registry_current is not None:
        return registry_current
    return inferred


def _seasons_for_ingestion(
    league_catalog: dict,
    league_id: int,
    headers: dict,
    errors: list[str],
    current_season: int | None = None,
    history_seasons: int | None = None,
    season_type: str = "split_year",
) -> list[int]:
    """Return the list of API season years to ingest for this competition.

    Active season year comes from :func:`_resolve_current_season_year` (API ``current``
    flag first, then type inference, then optional registry override).

    Resolution order (first match wins):
    1. API_FOOTBALL_SEASON env var — single explicit season, no filtering.
    2. API_FOOTBALL_SEASONS env var — explicit comma-separated list, filtered to band.
    3. Full/paid ingest profile — discover all seasons from the API catalog, filter to band.
    4. Default profile — ``history_seasons`` band (current + prior seasons for form),
       capped at ``API_FOOTBALL_DEFAULT_PROFILE_MAX_SEASONS`` (default 3).
    5. Fallback — single resolved current season only.

    ``history_seasons`` in the registry sets how many season start years back from
    the resolved current season to include (e.g. 2 = current + one prior for form).
    """
    raw_single = os.getenv("API_FOOTBALL_SEASON", "").strip()
    if raw_single:
        return [int(raw_single)]

    resolved_current = _resolve_current_season_year(
        season_type=season_type,
        registry_current=current_season,
        league_catalog=league_catalog,
    )

    global_lo = effective_season_min()
    if history_seasons is not None and history_seasons >= 1:
        competition_lo = resolved_current - (history_seasons - 1)
        lo = max(global_lo, competition_lo)
    else:
        lo = global_lo
    hi = resolved_current
    fallback = resolved_current

    csv = os.getenv("API_FOOTBALL_SEASONS", "").strip()
    if csv:
        years: list[int] = []
        for x in csv.split(","):
            x = x.strip()
            if not x:
                continue
            years.append(int(x))
        out = sorted({y for y in years if lo <= y <= hi})
        if not out and years:
            errors.append(
                "API_FOOTBALL_SEASONS: every year was outside "
                f"the active season band ({lo}..{hi}); using inferred single season"
            )
            return [fallback]
        return out or [fallback]

    want_multi = _ingest_profile_name() in ("full", "paid", "complete") or _env_truthy(
        "API_FOOTBALL_ALL_SEASONS"
    )
    if want_multi:
        discovered = list(_season_years_from_leagues_catalog(league_catalog, errors))
        if len(discovered) < 2:
            extra = _season_years_from_leagues_seasons_endpoint(headers, league_id, errors)
            discovered = sorted(set(discovered) | set(extra))
            if len(discovered) < 2:
                errors.append(
                    f"multi-season: only {len(discovered)} year(s) from /leagues and "
                    f"/leagues/seasons for league_id={league_id} — check API response and plan."
                )
        filt = [y for y in discovered if lo <= y <= hi]
        if not filt:
            if discovered:
                errors.append(
                    "multi-season: no API seasons fall inside "
                    f"the active season band ({lo}..{hi}); using inferred single season"
                )
            return [fallback]
        return filt

    band = list(range(lo, hi + 1))
    if history_seasons is not None and band:
        max_band = _default_profile_max_band_seasons()
        if len(band) <= max_band:
            return band

    return [fallback]


def _merge_merged_paged(dst: dict | None, src: dict) -> dict:
    """Merge ``fetch_merged_paged`` outputs (concatenate ``response`` / string ``errors``)."""
    if dst is None:
        out = dict(src)
        out["errors"] = list(out.get("errors") or [])
        out["response"] = list(out.get("response") or [])
        out["results"] = len(out["response"])
        out["paging"] = {"current": 1, "total": 1}
        return out
    dst["response"].extend(src.get("response") or [])
    dst["errors"].extend(list(src.get("errors") or []))
    dst["results"] = len(dst["response"])
    dst["paging"] = {"current": 1, "total": 1}
    return dst


def _merge_json_api(dst: dict | None, src: dict) -> dict:
    """Merge plain ``fetch_json`` envelopes (extend ``response`` list when applicable)."""
    if dst is None:
        d = dict(src)
        d["errors"] = list(_flatten_api_errors(src.get("errors")))
        return d
    prev = dst.get("response")
    nxt = src.get("response")
    if isinstance(prev, list) and isinstance(nxt, list):
        prev.extend(nxt)
    elif isinstance(prev, list) and nxt is not None:
        prev.append(nxt)
    elif prev is None and nxt is not None:
        dst["response"] = list(nxt) if isinstance(nxt, list) else [nxt]
    dst["errors"] = list(dst.get("errors") or []) + list(_flatten_api_errors(src.get("errors")))
    if isinstance(dst.get("response"), list):
        dst["results"] = len(dst["response"])
    return dst


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
    Defaults to **season** (``league`` + ``season`` only) so one run pulls the full competition
    calendar the API returns for that league (maximize data on free-friendly keys).

    ``from_to`` keeps a rolling or explicit date window. ``next`` is mainly for paid plans
    (free keys often reject ``next``).
    """
    mode = os.getenv("API_FOOTBALL_FIXTURES_MODE", "season").strip().lower()
    base = {"league": league_id, "season": season}
    if mode in ("season", "league", "full", "all"):
        return dict(base)
    if mode in ("from_to", "range", "daterange"):
        date_from = os.getenv("API_FOOTBALL_FIXTURE_FROM")
        date_to = os.getenv("API_FOOTBALL_FIXTURE_TO")
        if date_from and date_to:
            return {**base, "from": date_from.strip(), "to": date_to.strip()}
        # Default 42: ~6 weeks of matchdays when anchored at end of May (14 was often only 1–2 rounds).
        days = int(os.getenv("API_FOOTBALL_FIXTURE_RANGE_DAYS", "42"))
        start_s, end_s = _default_fixture_date_range(season, days)
        return {**base, "from": start_s, "to": end_s}
    if mode == "next":
        return {**base, "next": 20}
    raise ValueError(
        "API_FOOTBALL_FIXTURES_MODE must be 'season' (default), 'from_to', or 'next'"
    )
