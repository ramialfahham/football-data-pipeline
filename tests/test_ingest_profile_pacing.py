"""Tests for request pacing defaults per ingest profile (#897).

Production ran UNPACED for three weeks. `_apply_ingest_profile_defaults` set
``API_FOOTBALL_REQUEST_PAUSE_MS=0`` under the `full` profile, `dbt-scheduled.yml` sets no profile so
it inherited that zero, and the provider rejected calls against its per-minute limit on 10 of 18
nightly runs while every one reported success.

These tests exist because nothing asserted the value. That is the same failure mode as #892, where a
silently reverted default regressed for two months. They pin the effective pause, not just the
string, so a future change to either `settings.py` or `quota.py` has to face them.
"""

from __future__ import annotations

import os

import pytest

from ingestion.api_football.quota import _request_pause_seconds
from ingestion.api_football.settings import _apply_ingest_profile_defaults


@pytest.fixture(autouse=True)
def _restore_environ():
    """Undo every environment write these tests cause.

    `_apply_ingest_profile_defaults` writes to `os.environ` with `setdefault` for the whole profile
    bundle (ALL_SEASONS, page caps, fanout soft cap), not just the pause. monkeypatch only reverts
    what monkeypatch itself set, so without this the bundle leaks into later tests: it broke
    `test_wide_history_truncates_to_profile_cap_on_default_profile` when the suite ran in file order.
    """
    saved = os.environ.copy()
    yield
    os.environ.clear()
    os.environ.update(saved)

# Blueprint §4: 4 calls/sec caps the request rate at 240/min, against a measured 450/min ceiling.
BLUEPRINT_PAUSE_MS = "250"
BLUEPRINT_PAUSE_SECONDS = 0.25

# quota.py's free-tier fallback when the variable is unset (~9 calls/min under a 10/min limit).
ECONOMY_FALLBACK_SECONDS = 6.6


def _clear_pacing_env(monkeypatch):
    """Start from a genuinely unset environment, as a fresh CI runner would."""
    monkeypatch.delenv("API_FOOTBALL_REQUEST_PAUSE_MS", raising=False)
    monkeypatch.delenv("API_FOOTBALL_INGEST_PROFILE", raising=False)
    monkeypatch.delenv("API_FOOTBALL_PAID_FULL_LOAD", raising=False)


class TestFullProfilePacing:
    def test_production_config_is_paced(self, monkeypatch):
        # THE #897 REGRESSION TEST. This reproduces production exactly: dbt-scheduled.yml sets no
        # API_FOOTBALL_INGEST_PROFILE, so _ingest_profile_name() returns "full" by default. Before
        # the fix this pause was 0.0 and the nightly burst-limited itself.
        _clear_pacing_env(monkeypatch)
        _apply_ingest_profile_defaults()
        assert _request_pause_seconds() == BLUEPRINT_PAUSE_SECONDS
        assert _request_pause_seconds() > 0, "production must never run unpaced (#897)"

    def test_explicit_full_profile_gets_the_blueprint_pause(self, monkeypatch):
        _clear_pacing_env(monkeypatch)
        monkeypatch.setenv("API_FOOTBALL_INGEST_PROFILE", "full")
        _apply_ingest_profile_defaults()
        assert _request_pause_seconds() == BLUEPRINT_PAUSE_SECONDS

    def test_profile_aliases_get_the_blueprint_pause(self, monkeypatch):
        # "paid" and "complete" are accepted aliases of the full profile; they must not diverge.
        for alias in ("paid", "complete"):
            _clear_pacing_env(monkeypatch)
            monkeypatch.setenv("API_FOOTBALL_INGEST_PROFILE", alias)
            _apply_ingest_profile_defaults()
            assert _request_pause_seconds() == BLUEPRINT_PAUSE_SECONDS, alias

    def test_sets_the_documented_millisecond_value(self, monkeypatch):
        # Pins the stored value too, so docs quoting "250" cannot silently drift from the code.
        _clear_pacing_env(monkeypatch)
        _apply_ingest_profile_defaults()
        assert os.environ["API_FOOTBALL_REQUEST_PAUSE_MS"] == BLUEPRINT_PAUSE_MS


class TestExplicitOverrideStillWins:
    def test_explicit_value_beats_the_profile_default(self, monkeypatch):
        # setdefault semantics: an operator who sets the variable is obeyed. A local backfill that
        # deliberately wants a different rate must still be able to ask for one.
        _clear_pacing_env(monkeypatch)
        monkeypatch.setenv("API_FOOTBALL_REQUEST_PAUSE_MS", "1000")
        _apply_ingest_profile_defaults()
        assert _request_pause_seconds() == 1.0

    def test_explicit_zero_is_still_honoured(self, monkeypatch):
        # Zero remains reachable ON PURPOSE. The defect was inheriting it by omission, not the
        # ability to choose it.
        _clear_pacing_env(monkeypatch)
        monkeypatch.setenv("API_FOOTBALL_REQUEST_PAUSE_MS", "0")
        _apply_ingest_profile_defaults()
        assert _request_pause_seconds() == 0.0


class TestEconomyProfileUnchanged:
    def test_economy_keeps_free_tier_fallback(self, monkeypatch):
        # The economy profile bundles no defaults, so the variable stays unset and quota.py's
        # free-tier fallback applies. #897 must not have moved this.
        for profile in ("default", "economy", "free"):
            _clear_pacing_env(monkeypatch)
            monkeypatch.setenv("API_FOOTBALL_INGEST_PROFILE", profile)
            _apply_ingest_profile_defaults()
            assert _request_pause_seconds() == ECONOMY_FALLBACK_SECONDS, profile
