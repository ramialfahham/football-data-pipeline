"""Tests for request pacing defaults per ingest profile; they pin the effective pause."""

from __future__ import annotations

import os

import pytest

from ingestion.api_football.quota import _request_pause_seconds
from ingestion.api_football.settings import _apply_ingest_profile_defaults


@pytest.fixture(autouse=True)
def _restore_environ():
    """`_apply_ingest_profile_defaults` writes a bundle into `os.environ` monkeypatch cannot revert."""
    saved = os.environ.copy()
    yield
    os.environ.clear()
    os.environ.update(saved)

# 4 calls/sec caps the rate at 240/min, under the provider's 450/min (docs/data_contract.md).
FULL_PAUSE_MS = "250"
FULL_PAUSE_SECONDS = 0.25

# quota.py's free-tier fallback when the variable is unset (~9 calls/min under a 10/min limit).
ECONOMY_FALLBACK_SECONDS = 6.6


def _clear_pacing_env(monkeypatch):
    monkeypatch.delenv("API_FOOTBALL_REQUEST_PAUSE_MS", raising=False)
    monkeypatch.delenv("API_FOOTBALL_INGEST_PROFILE", raising=False)
    monkeypatch.delenv("API_FOOTBALL_PAID_FULL_LOAD", raising=False)


class TestFullProfilePacing:
    def test_production_config_is_paced(self, monkeypatch):
        # Production sets no API_FOOTBALL_INGEST_PROFILE, so the profile defaults to "full".
        _clear_pacing_env(monkeypatch)
        _apply_ingest_profile_defaults()
        assert _request_pause_seconds() == FULL_PAUSE_SECONDS
        assert _request_pause_seconds() > 0, "production must never run unpaced (#897)"

    def test_explicit_full_profile_gets_the_full_pause(self, monkeypatch):
        _clear_pacing_env(monkeypatch)
        monkeypatch.setenv("API_FOOTBALL_INGEST_PROFILE", "full")
        _apply_ingest_profile_defaults()
        assert _request_pause_seconds() == FULL_PAUSE_SECONDS

    def test_profile_aliases_get_the_full_pause(self, monkeypatch):
        # "paid" and "complete" are aliases of the full profile.
        for alias in ("paid", "complete"):
            _clear_pacing_env(monkeypatch)
            monkeypatch.setenv("API_FOOTBALL_INGEST_PROFILE", alias)
            _apply_ingest_profile_defaults()
            assert _request_pause_seconds() == FULL_PAUSE_SECONDS, alias

    def test_sets_the_documented_millisecond_value(self, monkeypatch):
        _clear_pacing_env(monkeypatch)
        _apply_ingest_profile_defaults()
        assert os.environ["API_FOOTBALL_REQUEST_PAUSE_MS"] == FULL_PAUSE_MS


class TestExplicitOverrideStillWins:
    def test_explicit_value_beats_the_profile_default(self, monkeypatch):
        # setdefault semantics: an operator who sets the variable is obeyed.
        _clear_pacing_env(monkeypatch)
        monkeypatch.setenv("API_FOOTBALL_REQUEST_PAUSE_MS", "1000")
        _apply_ingest_profile_defaults()
        assert _request_pause_seconds() == 1.0

    def test_explicit_zero_is_still_honoured(self, monkeypatch):
        # Zero stays reachable on purpose; only inheriting it by omission is wrong.
        _clear_pacing_env(monkeypatch)
        monkeypatch.setenv("API_FOOTBALL_REQUEST_PAUSE_MS", "0")
        _apply_ingest_profile_defaults()
        assert _request_pause_seconds() == 0.0


class TestEconomyProfileUnchanged:
    def test_economy_keeps_free_tier_fallback(self, monkeypatch):
        # The economy profile bundles no defaults, so quota.py's free-tier fallback applies.
        for profile in ("default", "economy", "free"):
            _clear_pacing_env(monkeypatch)
            monkeypatch.setenv("API_FOOTBALL_INGEST_PROFILE", profile)
            _apply_ingest_profile_defaults()
            assert _request_pause_seconds() == ECONOMY_FALLBACK_SECONDS, profile
