"""Infers the API season start year for split-year leagues and the default rolling season window."""

from __future__ import annotations

import os
from datetime import date, datetime

from .settings import DEFAULT_SEASON_WINDOW_YEARS


def _infer_competition_season_start_year(now: datetime | None = None) -> int:
    """Season start year assuming a 1 July boundary; wrong for calendar-year tournaments."""
    today = (now or datetime.utcnow()).date()
    if today >= date(today.year, 7, 1):
        return today.year
    return today.year - 1


def effective_season_min() -> int:
    """Default lower bound; an explicit history_seasons overrides it."""
    hi = _infer_competition_season_start_year()
    return hi - (DEFAULT_SEASON_WINDOW_YEARS - 1)


def effective_season_max() -> int:
    """Upper bound: the active campaign's season start year."""
    return _infer_competition_season_start_year()


def _default_season_min() -> int:
    return effective_season_min()


def _default_season_max() -> int:
    return effective_season_max()


def season_year() -> int:
    """API_FOOTBALL_SEASON if set, else the inferred season clamped to the default window."""
    raw = os.getenv("API_FOOTBALL_SEASON")
    if raw is not None and raw.strip() != "":
        return int(raw.strip())
    candidate = _infer_competition_season_start_year()
    lo = effective_season_min()
    hi = effective_season_max()
    return min(max(candidate, lo), hi)
