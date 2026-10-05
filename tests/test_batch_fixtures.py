"""Tests for ingestion/api_football/loads/batch_fixtures.py

All BigQuery and HTTP interactions are mocked — no live GCP connection required.
"""

from __future__ import annotations

from datetime import date, timedelta
from unittest.mock import MagicMock, patch

from ingestion.api_football.loads.batch_fixtures import (
    _BATCH_SIZE,
    _STATS_RETRY_DAYS,
    _finished_fixture_ids,
    _needs_fetch,
    run_batch_fixture_fanout_and_persist,
)
from ingestion.api_football.loads.context import CompetitionRunResult


def _covered(has_statistics: dict[int, bool], players: dict[int, bool] | None = None) -> dict:
    """One league's `read_coverage` entry: players covered unless its second fetch is due."""
    return {
        "FIXTURE_STATISTICS": has_statistics,
        "FIXTURE_PLAYERS": players if players is not None else dict.fromkeys(has_statistics, True),
    }


# ---------------------------------------------------------------------------
# _finished_fixture_ids
# ---------------------------------------------------------------------------


class TestFinishedFixtureIds:
    def _row(self, fid, status: str) -> dict:
        return {"fixture": {"id": fid, "status": {"short": status}}}

    def test_returns_ft_aet_pen(self):
        rows = [
            self._row(1, "FT"),
            self._row(2, "AET"),
            self._row(3, "PEN"),
            self._row(4, "NS"),
            self._row(5, "1H"),
            self._row(6, "HT"),
        ]
        assert _finished_fixture_ids(rows) == {1, 2, 3}

    def test_empty_response_returns_empty_set(self):
        assert _finished_fixture_ids([]) == set()

    def test_none_response_returns_empty_set(self):
        assert _finished_fixture_ids(None) == set()

    def test_skips_row_with_no_fixture_id(self):
        rows = [{"fixture": {"status": {"short": "FT"}}}]
        assert _finished_fixture_ids(rows) == set()

    def test_casts_string_ids_to_int(self):
        rows = [{"fixture": {"id": "42", "status": {"short": "FT"}}}]
        assert 42 in _finished_fixture_ids(rows)

    def test_skips_rows_missing_fixture_key(self):
        rows = [{"teams": {"home": {"id": 1}}}]
        assert _finished_fixture_ids(rows) == set()

    def test_status_comparison_is_case_insensitive(self):
        rows = [{"fixture": {"id": 99, "status": {"short": "ft"}}}]
        assert 99 in _finished_fixture_ids(rows)


# ---------------------------------------------------------------------------
# _needs_fetch
# ---------------------------------------------------------------------------


class TestNeedsFetch:
    TODAY = date(2026, 5, 26)
    CUTOFF = TODAY - timedelta(days=_STATS_RETRY_DAYS)

    def test_never_fetched_always_needs_fetch(self):
        assert _needs_fetch(1, {}, {1: self.TODAY}, self.CUTOFF) is True

    def test_never_fetched_no_kickoff_still_needs_fetch(self):
        assert _needs_fetch(1, {}, {}, self.CUTOFF) is True

    def test_fetched_with_statistics_is_done(self):
        assert _needs_fetch(1, _covered({1: True}), {1: self.TODAY}, self.CUTOFF) is False

    def test_second_fetch_due_with_statistics_fetches(self):
        covered = _covered({1: True}, players={1: False})
        assert _needs_fetch(1, covered, {1: self.TODAY}, self.CUTOFF) is True

    def test_second_fetch_due_with_empty_stats_past_window_fetches(self):
        kickoff = self.CUTOFF - timedelta(days=1)
        covered = _covered({1: False}, players={1: False})
        assert _needs_fetch(1, covered, {1: kickoff}, self.CUTOFF) is True

    def test_second_fetch_due_without_kickoff_in_fixtures_fetches(self):
        """Due is decided by the coverage read; the fixtures payload's kickoff is not needed."""
        covered = _covered({1: True}, players={1: False})
        assert _needs_fetch(1, covered, {}, self.CUTOFF) is True

    def test_empty_stats_kickoff_exactly_at_cutoff_retries(self):
        """Kickoff on the cutoff day is still within the retry window (>= cutoff)."""
        assert _needs_fetch(1, _covered({1: False}), {1: self.CUTOFF}, self.CUTOFF) is True

    def test_empty_stats_kickoff_one_day_before_cutoff_skips(self):
        """Kickoff one day before the cutoff is past the retry window."""
        kickoff = self.CUTOFF - timedelta(days=1)
        assert _needs_fetch(1, _covered({1: False}), {1: kickoff}, self.CUTOFF) is False

    def test_empty_stats_kickoff_after_cutoff_retries(self):
        kickoff = self.TODAY  # recent match
        assert _needs_fetch(1, _covered({1: False}), {1: kickoff}, self.CUTOFF) is True

    def test_empty_stats_no_kickoff_skips(self):
        """If kickoff is unknown, can't determine window — skip to be safe."""
        assert _needs_fetch(1, _covered({1: False}), {}, self.CUTOFF) is False


# ---------------------------------------------------------------------------
# run_batch_fixture_fanout_and_persist
# ---------------------------------------------------------------------------


class TestRunBatchFixtureFanoutAndPersist:
    """Integration-level tests with mocked BQ client and HTTP layer."""

    def _make_fixture_row(
        self,
        fid: int,
        status: str = "FT",
        kickoff: str = "2026-05-20T18:00:00+00:00",
    ) -> dict:
        return {
            "fixture": {
                "id": fid,
                "date": kickoff,
                "status": {"short": status},
            }
        }

    def _make_result(self, league_code: str, fixture_rows: list) -> MagicMock:
        result = MagicMock()
        result.league_code = league_code
        result.fixtures_merged = {"response": fixture_rows}
        return result

    def _make_ctx(self, client):
        ctx = MagicMock()
        ctx.client = client
        ctx.headers = {"x-apisports-key": "test-key"}
        ctx.errors = []
        return ctx

    def test_no_api_calls_when_all_fixtures_done(self):
        """All finished fixtures already have statistics → no HTTP calls, and no read of its own."""
        client = MagicMock()
        covered = {"BL1": _covered({100: True})}

        ctx = self._make_ctx(client)
        result = self._make_result("BL1", [self._make_fixture_row(100, "FT")])

        with patch("ingestion.api_football.loads.batch_fixtures.fetch_json") as mock_fetch:
            with patch("ingestion.api_football.loads.batch_fixtures._insert_fixture_rows"):
                run_batch_fixture_fanout_and_persist(ctx, [result], covered)

        mock_fetch.assert_not_called()
        client.query.assert_not_called()

    def test_fetches_fixture_due_its_second_fetch(self):
        """A fixture with statistics whose player stats' second fetch is due is fetched again."""
        client = MagicMock()
        covered = {"WC": _covered({100: True, 101: True}, players={100: False, 101: True})}

        ctx = self._make_ctx(client)
        result = self._make_result(
            "WC", [self._make_fixture_row(100, "FT"), self._make_fixture_row(101, "FT")]
        )

        fetch_resp = {"response": [], "errors": [], "results": 0}
        with patch(
            "ingestion.api_football.loads.batch_fixtures.fetch_json",
            return_value=fetch_resp,
        ) as mock_fetch:
            with patch("ingestion.api_football.loads.batch_fixtures._insert_fixture_rows"):
                with patch.dict("os.environ", {"API_FOOTBALL_BATCH_SLEEP_MS": "0"}):
                    run_batch_fixture_fanout_and_persist(ctx, [result], covered)

        mock_fetch.assert_called_once()
        assert mock_fetch.call_args[1]["params"]["ids"] == "100"

    def test_no_api_calls_when_no_finished_fixtures(self):
        """Only upcoming fixtures → nothing to fetch."""
        client = MagicMock()
        covered: dict = {}

        ctx = self._make_ctx(client)
        result = self._make_result("BL1", [self._make_fixture_row(1, "NS")])

        with patch("ingestion.api_football.loads.batch_fixtures.fetch_json") as mock_fetch:
            with patch("ingestion.api_football.loads.batch_fixtures._insert_fixture_rows"):
                run_batch_fixture_fanout_and_persist(ctx, [result], covered)

        mock_fetch.assert_not_called()

    def test_fetches_all_unfetched_finished_fixtures(self):
        """All fixture IDs from a competition with no prior data are fetched in one batch."""
        client = MagicMock()
        covered: dict = {}

        ctx = self._make_ctx(client)
        rows = [self._make_fixture_row(i, "FT") for i in range(1, 4)]
        result = self._make_result("BL1", rows)

        fetch_resp = {"response": [], "errors": [], "results": 0}
        with patch(
            "ingestion.api_football.loads.batch_fixtures.fetch_json",
            return_value=fetch_resp,
        ) as mock_fetch:
            with patch("ingestion.api_football.loads.batch_fixtures._insert_fixture_rows"):
                with patch.dict("os.environ", {"API_FOOTBALL_BATCH_SLEEP_MS": "0"}):
                    run_batch_fixture_fanout_and_persist(ctx, [result], covered)

        assert mock_fetch.call_count == 1
        params = mock_fetch.call_args[1]["params"]
        fetched_ids = {int(x) for x in params["ids"].split("-")}
        assert fetched_ids == {1, 2, 3}

    def test_splits_into_multiple_batches_above_batch_size(self):
        """More than _BATCH_SIZE fixtures trigger multiple API calls."""
        client = MagicMock()
        covered: dict = {}

        ctx = self._make_ctx(client)
        # BATCH_SIZE + 5 fixtures → 2 calls (BATCH_SIZE + 5)
        n = _BATCH_SIZE + 5
        rows = [self._make_fixture_row(i, "FT") for i in range(1, n + 1)]
        result = self._make_result("BL1", rows)

        fetch_resp = {"response": [], "errors": [], "results": 0}
        with patch(
            "ingestion.api_football.loads.batch_fixtures.fetch_json",
            return_value=fetch_resp,
        ) as mock_fetch:
            with patch("ingestion.api_football.loads.batch_fixtures._insert_fixture_rows"):
                with patch.dict("os.environ", {"API_FOOTBALL_BATCH_SLEEP_MS": "0"}):
                    run_batch_fixture_fanout_and_persist(ctx, [result], covered)

        assert mock_fetch.call_count == 2
        # First batch: exactly BATCH_SIZE ids
        first_ids = mock_fetch.call_args_list[0][1]["params"]["ids"].split("-")
        assert len(first_ids) == _BATCH_SIZE
        # Second batch: remaining 5
        second_ids = mock_fetch.call_args_list[1][1]["params"]["ids"].split("-")
        assert len(second_ids) == 5

    def test_sleeps_between_calls_not_before_first(self):
        """Sleep is called once between two calls, not before the first."""
        client = MagicMock()
        covered: dict = {}

        ctx = self._make_ctx(client)
        n = _BATCH_SIZE + 1  # exactly 2 batches
        rows = [self._make_fixture_row(i, "FT") for i in range(1, n + 1)]
        result = self._make_result("BL1", rows)

        fetch_resp = {"response": [], "errors": [], "results": 0}
        with patch(
            "ingestion.api_football.loads.batch_fixtures.fetch_json",
            return_value=fetch_resp,
        ):
            with patch("ingestion.api_football.loads.batch_fixtures._insert_fixture_rows"):
                with patch(
                    "ingestion.api_football.loads.batch_fixtures.time.sleep"
                ) as mock_sleep:
                    with patch.dict(
                        "os.environ", {"API_FOOTBALL_BATCH_SLEEP_MS": "250"}
                    ):
                        run_batch_fixture_fanout_and_persist(ctx, [result], covered)

        assert mock_sleep.call_count == 1
        mock_sleep.assert_called_once_with(0.25)

    def test_no_sleep_when_only_one_batch(self):
        """No sleep is needed when there is only one API call."""
        client = MagicMock()
        covered: dict = {}

        ctx = self._make_ctx(client)
        rows = [self._make_fixture_row(1, "FT")]
        result = self._make_result("BL1", rows)

        fetch_resp = {"response": [], "errors": [], "results": 0}
        with patch(
            "ingestion.api_football.loads.batch_fixtures.fetch_json",
            return_value=fetch_resp,
        ):
            with patch("ingestion.api_football.loads.batch_fixtures._insert_fixture_rows"):
                with patch(
                    "ingestion.api_football.loads.batch_fixtures.time.sleep"
                ) as mock_sleep:
                    with patch.dict(
                        "os.environ", {"API_FOOTBALL_BATCH_SLEEP_MS": "250"}
                    ):
                        run_batch_fixture_fanout_and_persist(ctx, [result], covered)

        mock_sleep.assert_not_called()

    def test_stops_on_quota_exhausted(self):
        """After quota is exhausted, remaining batches are skipped."""
        import ingestion.api_football.quota as quota_mod

        client = MagicMock()
        covered: dict = {}

        ctx = self._make_ctx(client)
        n = _BATCH_SIZE + 5  # would be 2 batches without early exit
        rows = [self._make_fixture_row(i, "FT") for i in range(1, n + 1)]
        result = self._make_result("BL1", rows)

        call_count = 0

        def exhausting_fetch(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            quota_mod._http_quota_exhausted = True
            return {"response": [], "errors": [], "results": 0}

        prev = quota_mod._http_quota_exhausted
        try:
            with patch(
                "ingestion.api_football.loads.batch_fixtures.fetch_json",
                side_effect=exhausting_fetch,
            ):
                with patch("ingestion.api_football.loads.batch_fixtures._insert_fixture_rows"):
                    with patch.dict("os.environ", {"API_FOOTBALL_BATCH_SLEEP_MS": "0"}):
                        run_batch_fixture_fanout_and_persist(ctx, [result], covered)
        finally:
            quota_mod._http_quota_exhausted = prev

        assert call_count == 1  # stopped after first batch exhausted quota

    def test_skips_empty_stats_fixtures_past_retry_window(self):
        """Fixtures fetched with empty stats more than STATS_RETRY_DAYS ago are not retried."""
        client = MagicMock()
        old_kickoff = date.today() - timedelta(days=_STATS_RETRY_DAYS + 2)

        covered = {"BL1": _covered({100: False})}  # empty stats, but old

        ctx = self._make_ctx(client)
        # Kickoff is old — past the retry window
        kickoff_str = old_kickoff.isoformat() + "T18:00:00+00:00"
        result = self._make_result("BL1", [self._make_fixture_row(100, "FT", kickoff_str)])

        with patch("ingestion.api_football.loads.batch_fixtures.fetch_json") as mock_fetch:
            with patch("ingestion.api_football.loads.batch_fixtures._insert_fixture_rows"):
                run_batch_fixture_fanout_and_persist(ctx, [result], covered)

        mock_fetch.assert_not_called()

    def test_retries_empty_stats_fixtures_within_retry_window(self):
        """Fixtures with empty stats within the retry window are re-fetched."""
        client = MagicMock()
        recent_kickoff = date.today() - timedelta(days=1)  # 1 day ago, within 3-day window

        covered = {"BL1": _covered({100: False})}

        ctx = self._make_ctx(client)
        kickoff_str = recent_kickoff.isoformat() + "T18:00:00+00:00"
        result = self._make_result("BL1", [self._make_fixture_row(100, "FT", kickoff_str)])

        fetch_resp = {"response": [], "errors": [], "results": 0}
        with patch(
            "ingestion.api_football.loads.batch_fixtures.fetch_json",
            return_value=fetch_resp,
        ) as mock_fetch:
            with patch("ingestion.api_football.loads.batch_fixtures._insert_fixture_rows"):
                with patch.dict("os.environ", {"API_FOOTBALL_BATCH_SLEEP_MS": "0"}):
                    run_batch_fixture_fanout_and_persist(ctx, [result], covered)

        mock_fetch.assert_called_once()

    def test_exception_in_batch_appended_to_errors(self):
        """An exception during a batch fetch is caught and added to errors."""
        client = MagicMock()
        covered: dict = {}

        ctx = self._make_ctx(client)
        result = self._make_result("BL1", [self._make_fixture_row(1, "FT")])

        with patch(
            "ingestion.api_football.loads.batch_fixtures.fetch_json",
            side_effect=RuntimeError("network failure"),
        ):
            with patch("ingestion.api_football.loads.batch_fixtures._insert_fixture_rows"):
                with patch.dict("os.environ", {"API_FOOTBALL_BATCH_SLEEP_MS": "0"}):
                    run_batch_fixture_fanout_and_persist(ctx, [result], covered)

        assert any("batch_fixtures" in e and "BL1" in e for e in ctx.errors)

    def test_multiple_competitions_planned_before_fetching(self):
        """Results from multiple competitions are all planned before any HTTP call."""
        client = MagicMock()
        covered: dict = {}

        ctx = self._make_ctx(client)
        result_bl1 = self._make_result("BL1", [self._make_fixture_row(1, "FT")])
        result_pl = self._make_result("PL", [self._make_fixture_row(2, "FT")])

        fetched_calls = []
        fetch_resp = {"response": [], "errors": [], "results": 0}

        def recording_fetch(*args, **kwargs):
            fetched_calls.append(kwargs.get("params", {}).get("ids"))
            return fetch_resp

        with patch(
            "ingestion.api_football.loads.batch_fixtures.fetch_json",
            side_effect=recording_fetch,
        ):
            with patch("ingestion.api_football.loads.batch_fixtures._insert_fixture_rows"):
                with patch.dict("os.environ", {"API_FOOTBALL_BATCH_SLEEP_MS": "0"}):
                    run_batch_fixture_fanout_and_persist(ctx, [result_bl1, result_pl], covered)

        assert len(fetched_calls) == 2
        all_ids = {int(fid) for call in fetched_calls for fid in call.split("-")}
        assert all_ids == {1, 2}


# ---------------------------------------------------------------------------
# Idle (poll-mode) competitions reach the fixture-details step
# ---------------------------------------------------------------------------


class TestIdleCompetitionsReachTheDetailsStep:
    def test_run_poll_phases_returns_the_competitions_fixtures(self):
        from ingestion.api_football.loads import competition_runner as cr

        fixtures = {"response": [{"fixture": {"id": 7, "status": {"short": "FT"}}}]}
        with patch.object(
            cr, "fetch_catalog_persist_and_plan", return_value=([2026], 2026, {"players": True})
        ), patch.object(
            cr, "fetch_merge_and_persist_fixtures", return_value=(fixtures, {1, 2}, {7})
        ):
            result = cr.run_poll_phases(MagicMock(), "WC", 1, current_season=2026)

        assert isinstance(result, CompetitionRunResult)
        assert result.league_code == "WC"
        assert result.fixtures_merged is fixtures
        assert result.team_ids == {1, 2}
        assert result.seasons_list == [2026]

    def test_orchestrator_hands_idle_competitions_and_the_coverage_read_to_the_step(self):
        """Structural, as in test_ingestion_read_hoisting.py: driving `_load_api_football` end to
        end means mocking every collaborator."""
        import ast
        import inspect
        import textwrap

        from ingestion.api_football import orchestrator

        tree = ast.parse(textwrap.dedent(inspect.getsource(orchestrator._load_api_football)))
        calls = [
            n for n in ast.walk(tree)
            if isinstance(n, ast.Call)
            and getattr(n.func, "id", None) == "run_batch_fixture_fanout_and_persist"
        ]
        assert len(calls) == 1
        args = [ast.unparse(a) for a in calls[0].args]
        assert "idle_results" in args[1]
        assert args[2] == "phase1_covered"
        idle_appends = {
            ast.unparse(n) for n in ast.walk(tree)
            if isinstance(n, ast.Call)
            and isinstance(n.func, ast.Attribute)
            and n.func.attr == "append"
            and ast.unparse(n.func.value) == "idle_results"
        }
        assert idle_appends == {"idle_results.append(poll_result)"}
