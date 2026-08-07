"""Tests for ingestion/api_football/loads/batch_fixtures.py

All BigQuery and HTTP interactions are mocked — no live GCP connection required.
"""

from __future__ import annotations

from datetime import date, timedelta
from unittest.mock import MagicMock, patch

from google.cloud.exceptions import NotFound

from ingestion.api_football.loads.batch_fixtures import (
    _BATCH_SIZE,
    _STATS_RETRY_DAYS,
    _finished_fixture_ids,
    _needs_fetch,
    _read_fetched_coverage,
    run_batch_fixture_fanout_and_persist,
)


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
        assert _needs_fetch(1, {1: True}, {1: self.TODAY}, self.CUTOFF) is False

    def test_empty_stats_kickoff_exactly_at_cutoff_retries(self):
        """Kickoff on the cutoff day is still within the retry window (>= cutoff)."""
        assert _needs_fetch(1, {1: False}, {1: self.CUTOFF}, self.CUTOFF) is True

    def test_empty_stats_kickoff_one_day_before_cutoff_skips(self):
        """Kickoff one day before the cutoff is past the retry window."""
        kickoff = self.CUTOFF - timedelta(days=1)
        assert _needs_fetch(1, {1: False}, {1: kickoff}, self.CUTOFF) is False

    def test_empty_stats_kickoff_after_cutoff_retries(self):
        kickoff = self.TODAY  # recent match
        assert _needs_fetch(1, {1: False}, {1: kickoff}, self.CUTOFF) is True

    def test_empty_stats_no_kickoff_skips(self):
        """If kickoff is unknown, can't determine window — skip to be safe."""
        assert _needs_fetch(1, {1: False}, {}, self.CUTOFF) is False


# ---------------------------------------------------------------------------
# _read_fetched_coverage
# ---------------------------------------------------------------------------


class TestReadFetchedCoverage:
    def _make_row(self, fixture_id, has_statistics: bool):
        row = MagicMock()
        row.fixture_id = fixture_id
        row.has_statistics = has_statistics
        return row

    def test_returns_empty_dict_when_table_not_found(self):
        client = MagicMock()
        client.get_table.side_effect = NotFound("table missing")
        result = _read_fetched_coverage(client, "BL1")
        assert result == {}
        client.query.assert_not_called()

    def test_returns_empty_dict_when_query_raises(self):
        client = MagicMock()
        client.get_table.return_value = MagicMock()
        client.query.side_effect = Exception("BQ error")
        result = _read_fetched_coverage(client, "BL1")
        assert result == {}

    def test_maps_fixture_id_to_has_statistics(self):
        client = MagicMock()
        client.get_table.return_value = MagicMock()
        client.query.return_value.result.return_value = [
            self._make_row(100, True),
            self._make_row(200, False),
        ]
        result = _read_fetched_coverage(client, "BL1")
        assert result[100] is True
        assert result[200] is False

    def test_fixture_ids_are_cast_to_int(self):
        client = MagicMock()
        client.get_table.return_value = MagicMock()
        client.query.return_value.result.return_value = [
            self._make_row("12345", True),
        ]
        result = _read_fetched_coverage(client, "BL1")
        assert 12345 in result
        assert isinstance(list(result.keys())[0], int)

    def test_empty_table_returns_empty_dict(self):
        client = MagicMock()
        client.get_table.return_value = MagicMock()
        client.query.return_value.result.return_value = []
        result = _read_fetched_coverage(client, "BL1")
        assert result == {}

    def test_query_contains_correct_table_id(self):
        """The BQ query must target the unified FIXTURE_DETAILS table, filtered by league_code."""
        client = MagicMock()
        client.get_table.return_value = MagicMock()
        client.query.return_value.result.return_value = []
        _read_fetched_coverage(client, "WC")
        query_sql = client.query.call_args[0][0]
        assert "RAW_APIF_FIXTURE_DETAILS" in query_sql
        assert "league_code = 'WC'" in query_sql


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
        """All finished fixtures already have statistics → no HTTP calls."""
        client = MagicMock()
        client.get_table.return_value = MagicMock()
        done_row = MagicMock()
        done_row.fixture_id = 100
        done_row.has_statistics = True
        client.query.return_value.result.return_value = [done_row]

        ctx = self._make_ctx(client)
        result = self._make_result("BL1", [self._make_fixture_row(100, "FT")])

        with patch("ingestion.api_football.loads.batch_fixtures.fetch_json") as mock_fetch:
            with patch("ingestion.api_football.loads.batch_fixtures._insert_fixture_rows"):
                run_batch_fixture_fanout_and_persist(ctx, [result])

        mock_fetch.assert_not_called()

    def test_no_api_calls_when_no_finished_fixtures(self):
        """Only upcoming fixtures → nothing to fetch."""
        client = MagicMock()
        client.get_table.side_effect = NotFound("no table")

        ctx = self._make_ctx(client)
        result = self._make_result("BL1", [self._make_fixture_row(1, "NS")])

        with patch("ingestion.api_football.loads.batch_fixtures.fetch_json") as mock_fetch:
            with patch("ingestion.api_football.loads.batch_fixtures._insert_fixture_rows"):
                run_batch_fixture_fanout_and_persist(ctx, [result])

        mock_fetch.assert_not_called()

    def test_fetches_all_unfetched_finished_fixtures(self):
        """All fixture IDs from a competition with no prior data are fetched in one batch."""
        client = MagicMock()
        client.get_table.side_effect = NotFound("no table")

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
                    run_batch_fixture_fanout_and_persist(ctx, [result])

        assert mock_fetch.call_count == 1
        params = mock_fetch.call_args[1]["params"]
        fetched_ids = {int(x) for x in params["ids"].split("-")}
        assert fetched_ids == {1, 2, 3}

    def test_splits_into_multiple_batches_above_batch_size(self):
        """More than _BATCH_SIZE fixtures trigger multiple API calls."""
        client = MagicMock()
        client.get_table.side_effect = NotFound("no table")

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
                    run_batch_fixture_fanout_and_persist(ctx, [result])

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
        client.get_table.side_effect = NotFound("no table")

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
                        run_batch_fixture_fanout_and_persist(ctx, [result])

        assert mock_sleep.call_count == 1
        mock_sleep.assert_called_once_with(0.25)

    def test_no_sleep_when_only_one_batch(self):
        """No sleep is needed when there is only one API call."""
        client = MagicMock()
        client.get_table.side_effect = NotFound("no table")

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
                        run_batch_fixture_fanout_and_persist(ctx, [result])

        mock_sleep.assert_not_called()

    def test_stops_on_quota_exhausted(self):
        """After quota is exhausted, remaining batches are skipped."""
        import ingestion.api_football.quota as quota_mod

        client = MagicMock()
        client.get_table.side_effect = NotFound("no table")

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
                        run_batch_fixture_fanout_and_persist(ctx, [result])
        finally:
            quota_mod._http_quota_exhausted = prev

        assert call_count == 1  # stopped after first batch exhausted quota

    def test_skips_empty_stats_fixtures_past_retry_window(self):
        """Fixtures fetched with empty stats more than STATS_RETRY_DAYS ago are not retried."""
        client = MagicMock()
        client.get_table.return_value = MagicMock()
        old_kickoff = date.today() - timedelta(days=_STATS_RETRY_DAYS + 2)

        stale_row = MagicMock()
        stale_row.fixture_id = 100
        stale_row.has_statistics = False  # empty stats, but old
        client.query.return_value.result.return_value = [stale_row]

        ctx = self._make_ctx(client)
        # Kickoff is old — past the retry window
        kickoff_str = old_kickoff.isoformat() + "T18:00:00+00:00"
        result = self._make_result("BL1", [self._make_fixture_row(100, "FT", kickoff_str)])

        with patch("ingestion.api_football.loads.batch_fixtures.fetch_json") as mock_fetch:
            with patch("ingestion.api_football.loads.batch_fixtures._insert_fixture_rows"):
                run_batch_fixture_fanout_and_persist(ctx, [result])

        mock_fetch.assert_not_called()

    def test_retries_empty_stats_fixtures_within_retry_window(self):
        """Fixtures with empty stats within the retry window are re-fetched."""
        client = MagicMock()
        client.get_table.return_value = MagicMock()
        recent_kickoff = date.today() - timedelta(days=1)  # 1 day ago, within 3-day window

        recent_row = MagicMock()
        recent_row.fixture_id = 100
        recent_row.has_statistics = False
        client.query.return_value.result.return_value = [recent_row]

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
                    run_batch_fixture_fanout_and_persist(ctx, [result])

        mock_fetch.assert_called_once()

    def test_exception_in_batch_appended_to_errors(self):
        """An exception during a batch fetch is caught and added to errors."""
        client = MagicMock()
        client.get_table.side_effect = NotFound("no table")

        ctx = self._make_ctx(client)
        result = self._make_result("BL1", [self._make_fixture_row(1, "FT")])

        with patch(
            "ingestion.api_football.loads.batch_fixtures.fetch_json",
            side_effect=RuntimeError("network failure"),
        ):
            with patch("ingestion.api_football.loads.batch_fixtures._insert_fixture_rows"):
                with patch.dict("os.environ", {"API_FOOTBALL_BATCH_SLEEP_MS": "0"}):
                    run_batch_fixture_fanout_and_persist(ctx, [result])

        assert any("batch_fixtures" in e and "BL1" in e for e in ctx.errors)

    def test_multiple_competitions_planned_before_fetching(self):
        """Results from multiple competitions are all planned before any HTTP call."""
        client = MagicMock()
        client.get_table.side_effect = NotFound("no table")

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
                    run_batch_fixture_fanout_and_persist(ctx, [result_bl1, result_pl])

        assert len(fetched_calls) == 2
        all_ids = {int(fid) for call in fetched_calls for fid in call.split("-")}
        assert all_ids == {1, 2}
