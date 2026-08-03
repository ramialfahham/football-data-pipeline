"""A run that drops API calls must not look clean (#898).

The 2026-08-02 nightly dropped 26 API calls and reported `conclusion: success`. So did 9 other runs
since 2026-07-16. Four independent causes, each pinned here:

1. The per-minute limit arrives as HTTP 200 with the error in the body, so `raise_for_status()` saw
   a healthy response and the 429 retry branch never fired. Zero retries.
2. `_payload_shows_daily_limit_exceeded` requires "day", so the per-minute class set no flag.
3. (not fixed here, out of scope) the completeness gate covers fanout entities only.
4. `ctx.errors` never reached the job summary.

The threshold policy is the CPO's, 2026-08-03: visible on every run, fail only when the same
endpoint drops on two consecutive runs. A single bad run must stay green, because failing skips the
dbt build and daily freshness is a hard requirement.
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


# The exact message the provider sends, from the 2026-08-02 nightly log.
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
        # The two detectors must not overlap: treating a per-minute limit as the daily cap would
        # abort every remaining call in the run.
        assert errors_quota._payload_shows_daily_limit_exceeded({"errors": _MINUTE_LIMIT}) is False

    def test_clean_response_is_neither(self):
        assert errors_quota._payload_shows_minute_rate_limit({"errors": []}) is False

    def test_detection_never_sets_the_daily_exhausted_flag(self):
        # THE DANGEROUS ONE. `_http_quota_exhausted` stops all remaining HTTP for the run. That is
        # right for a daily cap and catastrophic for a limit that clears within the minute.
        errors_quota._payload_shows_minute_rate_limit({"errors": _MINUTE_LIMIT})
        assert errors_quota._http_quota_exhausted is False


class TestDroppedCallsAreCountedByEndpoint:
    """Counted at the HTTP layer, once per call whose final attempt was still rejected.

    Review round 1 FAILED an earlier version that counted inside `append_api_errors`, keyed off the
    caller's context string. `loads/fixtures.py` appends per season AND again on the merged
    envelope, and `_merge_merged_paged` carries the earlier seasons' error text forward, so the
    same drop was counted twice. Counting where the call happens removes the whole class: the tally
    no longer depends on how many times any caller reports the same error.
    """

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
        # REGRESSION GUARD for the round 1 defect. `append_api_errors` must stay a pure reporter:
        # it is called twice against overlapping error data in loads/fixtures.py, so any counting
        # side effect there double-counts by construction.
        sink: list[str] = []
        errors_quota.append_api_errors({"errors": _MINUTE_LIMIT}, "fixtures BL1 season=2026", sink)
        errors_quota.append_api_errors({"errors": _MINUTE_LIMIT}, "fixtures BL1", sink)
        assert errors_quota.minute_rate_limit_counts() == {}
        assert len(sink) == 2  # reporting behaviour itself is unchanged


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
        # One HTTP call, rejected on both attempts, counts exactly one drop against its path.
        def fake_get(url, headers=None, params=None, timeout=None):
            return self._response({"errors": _MINUTE_LIMIT, "response": []})

        monkeypatch.setattr(http_client.requests, "get", fake_get)
        monkeypatch.setattr(http_client.time, "sleep", lambda s: None)
        monkeypatch.setattr(http_client, "_throttle", lambda: None)

        http_client.fetch_json("/players", {}, {"team": 1})
        assert errors_quota.minute_rate_limit_counts() == {"/players": 1}

    def test_a_call_rescued_by_the_retry_is_not_counted_as_dropped(self, monkeypatch):
        # Rejected then successful means no data was lost, so it must NOT inflate the drop count.
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
        # THE #898 REGRESSION TEST. Before the fix this returned on the first call with zero
        # retries, because status 200 skipped the 429 branch and raise_for_status() passed.
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
        # A second failure returns the failed body rather than looping. The caller then sees a
        # body-level error, which #896's `result_is_complete` reads as incomplete.
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
        # Once the daily cap is gone a retry cannot help, and it must still latch the flag that
        # stops the rest of the run.
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
        # The whole point of the CPO ruling: a transient limit self-heals, and failing would skip
        # the dbt build and cost daily freshness.
        assert detect_stagnant_dropped_calls({"players": 11}, {}) == []
        assert detect_stagnant_dropped_calls({"players": 11}, {"coaches": 3}) == []

    def test_same_endpoint_two_runs_running_fails(self):
        out = detect_stagnant_dropped_calls({"players": 4}, {"players": 11})
        assert out == [{"endpoint": "players", "prior_count": 11, "count": 4}]

    def test_healed_endpoint_does_not_fail(self):
        # Dropped last run, clean this run: healing, which is exactly what must NOT alarm.
        assert detect_stagnant_dropped_calls({}, {"players": 11}) == []

    def test_no_prior_run_is_silent(self):
        # First run, or a run after the snapshot was skipped. Fail-open, no false alarm.
        assert detect_stagnant_dropped_calls({"players": 11}, None) == []

    def test_reports_every_stagnant_endpoint(self):
        out = detect_stagnant_dropped_calls(
            {"players": 2, "coaches": 1, "transfers": 5},
            {"players": 3, "coaches": 2},
        )
        assert [s["endpoint"] for s in out] == ["coaches", "players"]


class TestGateRespectsTheOperatorKillSwitches:
    """Review round 1 FAILED an earlier version that ORed this signal into the exit condition in
    the orchestrator, bypassing both documented escape hatches.

    The pre-existing `stagnant_statistics` signal is subordinate to `report["skipped"]`
    (API_FOOTBALL_SKIP_COMPLETENESS_CHECK) and to `fail_on_incomplete()`
    (API_FOOTBALL_FAIL_ON_INCOMPLETE=0, the documented backfill override). A second stagnation
    signal sharing the same exit code must be subordinate to the same two, or an operator running
    the documented backfill playbook gets exit 3 anyway. A backfill is heavy on calls and is
    exactly when this would fire.
    """

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
        # The parameters are optional, so every existing caller keeps its behaviour.
        monkeypatch.delenv("API_FOOTBALL_FAIL_ON_INCOMPLETE", raising=False)
        out = evaluate_completeness_outcome(self._REPORT)
        assert out["stagnant_dropped_calls"] == []
        assert out["hard_fail"] is False
