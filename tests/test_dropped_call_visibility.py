"""A run that drops API calls must not look clean: drops are detected, retried, counted and gated.

Fail only when the same endpoint drops on two consecutive runs, since failing skips the dbt build.
"""

from __future__ import annotations

import pytest

from ingestion.api_football import http_client, quota as errors_quota
from ingestion.api_football.completeness import (
    detect_stagnant_dropped_calls,
    evaluate_completeness_outcome,
)


@pytest.fixture(autouse=True)
def _clean_run_state():
    """Both module globals are per-run state; a leak between tests would be a false signal."""
    errors_quota.reset_http_quota_exhausted()
    errors_quota.reset_minute_rate_limit_counts()
    yield
    errors_quota.reset_http_quota_exhausted()
    errors_quota.reset_minute_rate_limit_counts()


# The exact messages the provider sends.
_MINUTE_LIMIT = {
    "rateLimit": "Too many requests. You have exceeded the limit of requests per minute of your subscription."
}
_DAILY_LIMIT = {"requests": "You have reached the request limit for the day"}


class TestPerMinuteDetection:
    def test_detects_the_real_provider_message(self):
        assert errors_quota._payload_shows_minute_rate_limit({"errors": _MINUTE_LIMIT}) is True

    def test_daily_message_is_not_a_minute_limit(self):
        assert errors_quota._payload_shows_minute_rate_limit({"errors": _DAILY_LIMIT}) is False

    def test_minute_message_is_not_a_daily_limit(self):
        # Treating a per-minute limit as the daily cap would abort every remaining call in the run.
        assert errors_quota._payload_shows_daily_limit_exceeded({"errors": _MINUTE_LIMIT}) is False

    def test_clean_response_is_neither(self):
        assert errors_quota._payload_shows_minute_rate_limit({"errors": []}) is False

    def test_detection_never_sets_the_daily_exhausted_flag(self):
        # `_http_quota_exhausted` stops all HTTP for the run, which is wrong for a per-minute limit.
        errors_quota._payload_shows_minute_rate_limit({"errors": _MINUTE_LIMIT})
        assert errors_quota._http_quota_exhausted is False


class TestDroppedCallsAreCountedByEndpoint:
    """Counted at the HTTP layer, so the tally ignores how often a caller reports an error."""

    def test_counts_per_endpoint(self):
        errors_quota.record_minute_rate_limit("/players")
        errors_quota.record_minute_rate_limit("/players")
        errors_quota.record_minute_rate_limit("/coachs")
        assert errors_quota.minute_rate_limit_counts() == {"/players": 2, "/coachs": 1}

    def test_ordered_highest_first(self):
        for _ in range(3):
            errors_quota.record_minute_rate_limit("/players")
        errors_quota.record_minute_rate_limit("/transfers")
        assert list(errors_quota.minute_rate_limit_counts()) == ["/players", "/transfers"]

    def test_reset_clears_between_runs(self):
        errors_quota.record_minute_rate_limit("/players")
        assert errors_quota.minute_rate_limit_counts() == {"/players": 1}
        errors_quota.reset_minute_rate_limit_counts()
        assert errors_quota.minute_rate_limit_counts() == {}

    def test_append_api_errors_does_not_count(self):
        # `append_api_errors` is called twice on overlapping errors, so counting there double-counts.
        sink: list[str] = []
        errors_quota.append_api_errors({"errors": _MINUTE_LIMIT}, "fixtures BL1 season=2026", sink)
        errors_quota.append_api_errors({"errors": _MINUTE_LIMIT}, "fixtures BL1", sink)
        assert errors_quota.minute_rate_limit_counts() == {}
        assert len(sink) == 2


class TestRetryOnPerMinuteLimit:
    def _response(self, body, headers=None):
        class _R:
            status_code = 200

            def __init__(self):
                self.headers = headers or {}

            def raise_for_status(self):
                return None

            def json(self):
                return body

        return _R()

    def test_a_dropped_call_is_counted_once(self, monkeypatch):
        def fake_get(url, headers=None, params=None, timeout=None):
            return self._response({"errors": _MINUTE_LIMIT, "response": []})

        monkeypatch.setattr(http_client.requests, "get", fake_get)
        monkeypatch.setattr(http_client.time, "sleep", lambda s: None)
        monkeypatch.setattr(http_client, "_throttle", lambda: None)

        http_client.fetch_json("/players", {}, {"team": 1})
        assert errors_quota.minute_rate_limit_counts() == {"/players": 1}

    def test_a_call_rescued_by_the_retry_is_not_counted_as_dropped(self, monkeypatch):
        calls = {"n": 0}

        def fake_get(url, headers=None, params=None, timeout=None):
            calls["n"] += 1
            if calls["n"] == 1:
                return self._response({"errors": _MINUTE_LIMIT, "response": []})
            return self._response({"errors": [], "response": [{"player": {"id": 1}}]})

        monkeypatch.setattr(http_client.requests, "get", fake_get)
        monkeypatch.setattr(http_client.time, "sleep", lambda s: None)
        monkeypatch.setattr(http_client, "_throttle", lambda: None)

        http_client.fetch_json("/players", {}, {"team": 1})
        assert errors_quota.minute_rate_limit_counts() == {}

    def test_body_level_limit_is_retried_once(self, monkeypatch):
        # Status 200 skips the 429 branch, so the body-level limit needs its own retry.
        calls = {"n": 0}

        def fake_get(url, headers=None, params=None, timeout=None):
            calls["n"] += 1
            if calls["n"] == 1:
                return self._response({"errors": _MINUTE_LIMIT, "response": []})
            return self._response({"errors": [], "response": [{"player": {"id": 1}}]})

        monkeypatch.setattr(http_client.requests, "get", fake_get)
        monkeypatch.setattr(http_client.time, "sleep", lambda s: None)
        monkeypatch.setattr(http_client, "_throttle", lambda: None)

        data = http_client.fetch_json("/players", {}, {"team": 1})
        assert calls["n"] == 2, "a per-minute limit must be retried"
        assert data["response"] == [{"player": {"id": 1}}]

    def test_retry_is_attempted_only_once(self, monkeypatch):
        # A second failure returns the failed body, which `result_is_complete` reads as incomplete.
        calls = {"n": 0}

        def fake_get(url, headers=None, params=None, timeout=None):
            calls["n"] += 1
            return self._response({"errors": _MINUTE_LIMIT, "response": []})

        monkeypatch.setattr(http_client.requests, "get", fake_get)
        monkeypatch.setattr(http_client.time, "sleep", lambda s: None)
        monkeypatch.setattr(http_client, "_throttle", lambda: None)

        data = http_client.fetch_json("/players", {}, {"team": 1})
        assert calls["n"] == 2
        assert http_client._payload_shows_minute_rate_limit(data) is True

    def test_daily_limit_is_not_retried(self, monkeypatch):
        # A retry cannot help once the daily cap is gone, and the stop-the-run flag must latch.
        calls = {"n": 0}

        def fake_get(url, headers=None, params=None, timeout=None):
            calls["n"] += 1
            return self._response({"errors": _DAILY_LIMIT, "response": []})

        monkeypatch.setattr(http_client.requests, "get", fake_get)
        monkeypatch.setattr(http_client.time, "sleep", lambda s: None)
        monkeypatch.setattr(http_client, "_throttle", lambda: None)

        http_client.fetch_json("/players", {}, {"team": 1})
        assert calls["n"] == 1
        assert errors_quota._http_quota_exhausted is True

    def test_clean_response_is_not_retried(self, monkeypatch):
        calls = {"n": 0}

        def fake_get(url, headers=None, params=None, timeout=None):
            calls["n"] += 1
            return self._response({"errors": [], "response": []})

        monkeypatch.setattr(http_client.requests, "get", fake_get)
        monkeypatch.setattr(http_client.time, "sleep", lambda s: None)
        monkeypatch.setattr(http_client, "_throttle", lambda: None)

        http_client.fetch_json("/players", {}, {"team": 1})
        assert calls["n"] == 1


class TestStagnationGate:
    def test_one_bad_run_does_not_fail(self):
        # A transient limit self-heals, and failing would skip the dbt build and cost freshness.
        assert detect_stagnant_dropped_calls({"players": 11}, {}) == []
        assert detect_stagnant_dropped_calls({"players": 11}, {"coaches": 3}) == []

    def test_same_endpoint_two_runs_running_fails(self):
        out = detect_stagnant_dropped_calls({"players": 4}, {"players": 11})
        assert out == [{"endpoint": "players", "prior_count": 11, "count": 4}]

    def test_healed_endpoint_does_not_fail(self):
        assert detect_stagnant_dropped_calls({}, {"players": 11}) == []

    def test_no_prior_run_is_silent(self):
        # First run, or a run after the snapshot was skipped: fail open.
        assert detect_stagnant_dropped_calls({"players": 11}, None) == []

    def test_reports_every_stagnant_endpoint(self):
        out = detect_stagnant_dropped_calls(
            {"players": 2, "coaches": 1, "transfers": 5},
            {"players": 3, "coaches": 2},
        )
        assert [s["endpoint"] for s in out] == ["coaches", "players"]


class TestGateRespectsTheOperatorKillSwitches:
    """Like `stagnant_statistics`, it must obey `report["skipped"]` and `fail_on_incomplete()`."""

    _REPORT = {"leagues": {}}

    def test_stagnant_dropped_calls_hard_fails_by_default(self, monkeypatch):
        monkeypatch.delenv("API_FOOTBALL_FAIL_ON_INCOMPLETE", raising=False)
        out = evaluate_completeness_outcome(
            self._REPORT,
            dropped_calls={"/players": 4},
            prior_dropped_calls={"/players": 11},
        )
        assert out["stagnant_dropped_calls"]
        assert out["hard_fail"] is True

    def test_fail_on_incomplete_override_suppresses_the_fail(self, monkeypatch):
        monkeypatch.setenv("API_FOOTBALL_FAIL_ON_INCOMPLETE", "0")
        out = evaluate_completeness_outcome(
            self._REPORT,
            dropped_calls={"/players": 4},
            prior_dropped_calls={"/players": 11},
        )
        assert out["stagnant_dropped_calls"], "still reported, so it stays visible"
        assert out["hard_fail"] is False, "but must not fail a run that set the override"

    def test_skipped_report_suppresses_the_fail(self, monkeypatch):
        monkeypatch.delenv("API_FOOTBALL_FAIL_ON_INCOMPLETE", raising=False)
        out = evaluate_completeness_outcome(
            {"skipped": True},
            dropped_calls={"/players": 4},
            prior_dropped_calls={"/players": 11},
        )
        assert out["stagnant_dropped_calls"] == []
        assert out["hard_fail"] is False

    def test_one_bad_run_still_does_not_fail(self, monkeypatch):
        monkeypatch.delenv("API_FOOTBALL_FAIL_ON_INCOMPLETE", raising=False)
        out = evaluate_completeness_outcome(
            self._REPORT, dropped_calls={"/players": 11}, prior_dropped_calls={}
        )
        assert out["stagnant_dropped_calls"] == []
        assert out["hard_fail"] is False

    def test_absent_dropped_call_args_change_nothing(self, monkeypatch):
        monkeypatch.delenv("API_FOOTBALL_FAIL_ON_INCOMPLETE", raising=False)
        out = evaluate_completeness_outcome(self._REPORT)
        assert out["stagnant_dropped_calls"] == []
        assert out["hard_fail"] is False
