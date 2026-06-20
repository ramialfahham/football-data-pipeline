"""Tests for API-first season discovery in seasons._seasons_for_ingestion."""

from __future__ import annotations

from ingestion.api_football.seasons import (
    _api_current_season_year,
    _most_recent_completed_season_year,
    _resolve_current_season_year,
    _seasons_for_ingestion,
)


def _vl_catalog() -> dict:
  return {
      "response": [
          {
              "league": {"id": 244, "name": "Veikkausliiga"},
              "seasons": [
                  {"year": 2025, "current": False},
                  {"year": 2026, "current": True},
              ],
          }
      ]
  }


class TestApiCurrentSeasonYear:
    def test_reads_current_flag_from_catalog(self):
        assert _api_current_season_year(_vl_catalog()) == 2026


class TestResolveCurrentSeasonYear:
    def test_api_current_wins_over_stale_registry(self):
        assert (
            _resolve_current_season_year(
                season_type="calendar_year",
                registry_current=2025,
                league_catalog=_vl_catalog(),
            )
            == 2026
        )

    def test_completed_season_when_no_current_flag(self):
        catalog = {
            "response": [
                {
                    "seasons": [
                        {"year": 2024, "current": False, "end": "2024-05-31"},
                        {"year": 2025, "current": False, "end": "2025-05-31"},
                    ],
                }
            ]
        }
        assert _most_recent_completed_season_year(catalog) == 2025
        assert (
            _resolve_current_season_year(
                season_type="split_year",
                registry_current=2024,
                league_catalog=catalog,
            )
            == 2025
        )

    def test_split_year_uses_july_rule_when_api_missing(self, monkeypatch):
        monkeypatch.setattr(
            "ingestion.api_football.seasons.season_year",
            lambda: 2025,
        )
        assert (
            _resolve_current_season_year(
                season_type="split_year",
                registry_current=2024,
                league_catalog={"response": []},
            )
            == 2024
        )


class TestSeasonsForIngestion:
    def test_calendar_year_history_two_ingests_current_and_prior(self, monkeypatch):
        monkeypatch.delenv("API_FOOTBALL_SEASON", raising=False)
        monkeypatch.delenv("API_FOOTBALL_SEASONS", raising=False)
        monkeypatch.setenv("API_FOOTBALL_INGEST_PROFILE", "default")

        seasons = _seasons_for_ingestion(
            _vl_catalog(),
            league_id=244,
            headers={},
            errors=[],
            current_season=2025,
            history_seasons=2,
            season_type="calendar_year",
        )
        assert seasons == [2025, 2026]

    def test_wide_history_truncates_to_profile_cap_on_default_profile(self, monkeypatch):
        monkeypatch.delenv("API_FOOTBALL_SEASON", raising=False)
        monkeypatch.delenv("API_FOOTBALL_SEASONS", raising=False)
        monkeypatch.setenv("API_FOOTBALL_INGEST_PROFILE", "default")
        monkeypatch.setenv("API_FOOTBALL_DEFAULT_PROFILE_MAX_SEASONS", "3")

        catalog = {
            "response": [
                {
                    "seasons": [{"year": y, "current": y == 2025} for y in range(2016, 2026)],
                }
            ]
        }
        seasons = _seasons_for_ingestion(
            catalog,
            league_id=78,
            headers={},
            errors=[],
            current_season=None,
            history_seasons=10,
            season_type="split_year",
        )
        assert seasons == [2023, 2024, 2025]

    def test_full_profile_history_seasons_authoritative_below_default_floor(self, monkeypatch):
        # history_seasons is AUTHORITATIVE: under the full profile it reaches its full
        # configured depth even when the default-window floor would be higher (e.g. after
        # July 1, when effective_season_min would clamp to 2017). Regression for removing the
        # max(global_lo, competition_lo) clamp — PL must reach 2016 deterministically (hs=11,
        # provider current=2026).
        monkeypatch.delenv("API_FOOTBALL_SEASON", raising=False)
        monkeypatch.delenv("API_FOOTBALL_SEASONS", raising=False)
        monkeypatch.setenv("API_FOOTBALL_INGEST_PROFILE", "full")
        monkeypatch.setattr(
            "ingestion.api_football.seasons.effective_season_min", lambda: 2017
        )
        catalog = {
            "response": [
                {"seasons": [{"year": y, "current": y == 2026} for y in range(2016, 2027)]},
            ]
        }
        seasons = _seasons_for_ingestion(
            catalog,
            league_id=39,
            headers={},
            errors=[],
            current_season=None,
            history_seasons=11,
            season_type="split_year",
        )
        assert seasons == list(range(2016, 2027))

    def test_unset_history_seasons_falls_back_to_default_window(self, monkeypatch):
        # With no explicit history_seasons, the default-window floor still applies.
        monkeypatch.delenv("API_FOOTBALL_SEASON", raising=False)
        monkeypatch.delenv("API_FOOTBALL_SEASONS", raising=False)
        monkeypatch.setenv("API_FOOTBALL_INGEST_PROFILE", "full")
        monkeypatch.setattr(
            "ingestion.api_football.seasons.effective_season_min", lambda: 2020
        )
        catalog = {
            "response": [
                {"seasons": [{"year": y, "current": y == 2025} for y in range(2016, 2026)]},
            ]
        }
        seasons = _seasons_for_ingestion(
            catalog,
            league_id=39,
            headers={},
            errors=[],
            current_season=None,
            history_seasons=None,
            season_type="split_year",
        )
        assert seasons == list(range(2020, 2026))
