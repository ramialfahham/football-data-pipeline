"""Tests for season_inference.py — the July 1 split-year boundary and rolling window.

The July 1 boundary is subtle: get it wrong by one day and every competition ingests
the previous season instead of the current one. This has caused real bugs.
"""

from datetime import datetime

from ingestion.api_football.season_inference import (
    _infer_competition_season_start_year,
    effective_season_max,
    effective_season_min,
    season_year,
)
from ingestion.api_football.settings import DEFAULT_SEASON_WINDOW_YEARS


# ---------------------------------------------------------------------------
# _infer_competition_season_start_year — July 1 boundary
# ---------------------------------------------------------------------------

class TestInferCompetitionSeasonStartYear:
    def test_july_1_starts_new_season(self):
        assert _infer_competition_season_start_year(datetime(2024, 7, 1)) == 2024

    def test_june_30_still_previous_season(self):
        assert _infer_competition_season_start_year(datetime(2024, 6, 30)) == 2023

    def test_mid_season_january(self):
        # January 2025 is mid 2024/25 season
        assert _infer_competition_season_start_year(datetime(2025, 1, 15)) == 2024

    def test_last_day_of_season(self):
        # June 30 is last day before next season boundary
        assert _infer_competition_season_start_year(datetime(2025, 6, 30)) == 2024

    def test_first_day_of_new_season(self):
        assert _infer_competition_season_start_year(datetime(2025, 7, 1)) == 2025

    def test_december_is_current_year(self):
        assert _infer_competition_season_start_year(datetime(2024, 12, 31)) == 2024

    def test_no_argument_returns_int(self):
        # Just verify it returns an integer without crashing
        result = _infer_competition_season_start_year()
        assert isinstance(result, int)
        assert 2000 <= result <= 2100


# ---------------------------------------------------------------------------
# effective_season_min / effective_season_max — rolling window
# ---------------------------------------------------------------------------

class TestEffectiveSeasonWindow:
    def test_window_is_default_season_window_years_wide(self, monkeypatch):
        monkeypatch.setattr(
            "ingestion.api_football.season_inference._infer_competition_season_start_year",
            lambda now=None: 2024,
        )
        lo = effective_season_min()
        hi = effective_season_max()
        assert hi == 2024
        assert hi - lo == DEFAULT_SEASON_WINDOW_YEARS - 1

    def test_min_is_hi_minus_window(self, monkeypatch):
        monkeypatch.setattr(
            "ingestion.api_football.season_inference._infer_competition_season_start_year",
            lambda now=None: 2025,
        )
        assert effective_season_min() == 2025 - (DEFAULT_SEASON_WINDOW_YEARS - 1)


# ---------------------------------------------------------------------------
# season_year — explicit override beats inference
# ---------------------------------------------------------------------------

class TestSeasonYear:
    def test_env_override_wins(self, monkeypatch):
        monkeypatch.setenv("API_FOOTBALL_SEASON", "2019")
        assert season_year() == 2019

    def test_empty_env_uses_inferred(self, monkeypatch):
        monkeypatch.delenv("API_FOOTBALL_SEASON", raising=False)
        monkeypatch.setattr(
            "ingestion.api_football.season_inference._infer_competition_season_start_year",
            lambda now=None: 2024,
        )
        result = season_year()
        assert result == 2024

    def test_result_within_window(self, monkeypatch):
        monkeypatch.delenv("API_FOOTBALL_SEASON", raising=False)
        result = season_year()
        lo = effective_season_min()
        hi = effective_season_max()
        assert lo <= result <= hi
