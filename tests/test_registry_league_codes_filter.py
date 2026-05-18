"""Tests for API_FOOTBALL_LEAGUE_CODES allowlist in selected_competitions()."""

from __future__ import annotations

import pytest

from ingestion.api_football.registry import selected_competitions


def test_league_codes_filter_limits_selection(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_FOOTBALL_INCLUDE_IN_PROGRESS", "1")
    monkeypatch.setenv("API_FOOTBALL_LEAGUE_CODES", "PL,BL2")

    selected, _skipped = selected_competitions()
    codes = {c.league_code for c in selected}

    assert codes == {"PL", "BL2"}


def test_empty_league_codes_filter_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_FOOTBALL_LEAGUE_CODES", " , ")

    with pytest.raises(ValueError, match="no league codes"):
        selected_competitions()
