"""Season year inference for split-year domestic leagues and the v1 rolling window.

The API uses the competition start calendar year as its season identifier
(e.g. 2024 = the 2024/25 Bundesliga). Two concerns live here:

1. Split-year boundary — July 1 determines whether the new season has started.
   On or after July 1 → return this calendar year. Before → return year - 1.
   Only correct for split-year domestic leagues; international tournaments (WC,
   qualifiers) use current_season from the competition registry instead.

2. Rolling window — the v1 pipeline ingests the last V1_SEASON_WINDOW_YEARS
   season start years, inclusive of the active campaign. effective_season_min /
   effective_season_max expose these bounds for filtering discovered API seasons.
"""

from __future__ import annotations

import os
from datetime import date, datetime

from .settings import V1_SEASON_WINDOW_YEARS


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
