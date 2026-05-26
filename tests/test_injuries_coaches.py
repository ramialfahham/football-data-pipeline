"""Tests for loads/injuries.py and loads/coaches.py.

All BigQuery and HTTP interactions are mocked — no live GCP connection required.
"""

from __future__ import annotations

from unittest.mock import MagicMock, call, patch

import pytest

from ingestion.api_football.loads.injuries import load_injuries
from ingestion.api_football.loads.coaches import load_coaches


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_ctx(errors=None):
    ctx = MagicMock()
    ctx.errors = errors if errors is not None else []
    ctx.headers = {"x-apisports-key": "test"}
    return ctx


def _api_response(items: list, errors=None) -> dict:
    return {
        "response": items,
        "errors": errors or [],
        "results": len(items),
        "paging": {"current": 1, "total": 1},
    }


# ---------------------------------------------------------------------------
# load_injuries
# ---------------------------------------------------------------------------


class TestLoadInjuries:
    def test_calls_api_once_per_season(self):
        ctx = _make_ctx()
        with patch(
            "ingestion.api_football.loads.injuries.fetch_merged_paged",
            return_value=_api_response([]),
        ) as mock_fetch:
            with patch("ingestion.api_football.loads.injuries.load_json_to_bq"):
                load_injuries(ctx, "BL1", 78, [2024, 2023])

        assert mock_fetch.call_count == 2
        calls = mock_fetch.call_args_list
        assert calls[0][0][0] == "/injuries"
        assert calls[0][0][2] == {"league": 78, "season": 2024}
        assert calls[1][0][2] == {"league": 78, "season": 2023}

    def test_merges_all_seasons_into_one_bq_row(self):
        ctx = _make_ctx()
        season_2024 = _api_response([{"player": {"id": 1}}, {"player": {"id": 2}}])
        season_2023 = _api_response([{"player": {"id": 3}}])

        with patch(
            "ingestion.api_football.loads.injuries.fetch_merged_paged",
            side_effect=[season_2024, season_2023],
        ):
            with patch(
                "ingestion.api_football.loads.injuries.load_json_to_bq"
            ) as mock_bq:
                load_injuries(ctx, "BL1", 78, [2024, 2023])

        assert mock_bq.call_count == 1
        payload = mock_bq.call_args[0][2]
        assert payload["results"] == 3
        assert len(payload["response"]) == 3

    def test_writes_to_correct_table(self):
        ctx = _make_ctx()
        with patch(
            "ingestion.api_football.loads.injuries.fetch_merged_paged",
            return_value=_api_response([{"player": {"id": 1}}]),
        ):
            with patch(
                "ingestion.api_football.loads.injuries.load_json_to_bq"
            ) as mock_bq:
                load_injuries(ctx, "PL", 39, [2024])

        table_name = mock_bq.call_args[0][1]
        assert table_name == "RAW_APIF_PL_INJURIES"

    def test_uses_append_mode(self):
        ctx = _make_ctx()
        with patch(
            "ingestion.api_football.loads.injuries.fetch_merged_paged",
            return_value=_api_response([{"player": {"id": 1}}]),
        ):
            with patch(
                "ingestion.api_football.loads.injuries.load_json_to_bq"
            ) as mock_bq:
                load_injuries(ctx, "BL1", 78, [2024])

        kwargs = mock_bq.call_args[1]
        assert kwargs.get("append") is True

    def test_no_op_when_seasons_list_empty(self):
        ctx = _make_ctx()
        with patch(
            "ingestion.api_football.loads.injuries.fetch_merged_paged"
        ) as mock_fetch:
            with patch("ingestion.api_football.loads.injuries.load_json_to_bq") as mock_bq:
                load_injuries(ctx, "BL1", 78, [])

        mock_fetch.assert_not_called()
        mock_bq.assert_not_called()

    def test_skips_remaining_seasons_when_quota_exhausted(self):
        import ingestion.api_football.quota as quota_mod

        ctx = _make_ctx()
        prev = quota_mod._http_quota_exhausted
        quota_mod._http_quota_exhausted = True
        try:
            with patch(
                "ingestion.api_football.loads.injuries.fetch_merged_paged"
            ) as mock_fetch:
                with patch("ingestion.api_football.loads.injuries.load_json_to_bq"):
                    load_injuries(ctx, "BL1", 78, [2024, 2023])
        finally:
            quota_mod._http_quota_exhausted = prev

        mock_fetch.assert_not_called()

    def test_api_exception_appended_to_errors_and_continues(self):
        ctx = _make_ctx()

        def raise_on_first(path, headers, base_params, **kwargs):
            if base_params["season"] == 2024:
                raise RuntimeError("timeout")
            return _api_response([{"player": {"id": 9}}])

        with patch(
            "ingestion.api_football.loads.injuries.fetch_merged_paged",
            side_effect=raise_on_first,
        ):
            with patch("ingestion.api_football.loads.injuries.load_json_to_bq"):
                load_injuries(ctx, "BL1", 78, [2024, 2023])

        assert any("injuries" in e and "BL1" in e for e in ctx.errors)

    def test_bq_exception_appended_to_errors(self):
        ctx = _make_ctx()
        with patch(
            "ingestion.api_football.loads.injuries.fetch_merged_paged",
            return_value=_api_response([{"player": {"id": 1}}]),
        ):
            with patch(
                "ingestion.api_football.loads.injuries.load_json_to_bq",
                side_effect=RuntimeError("BQ write failed"),
            ):
                load_injuries(ctx, "BL1", 78, [2024])

        assert any("injuries BQ" in e for e in ctx.errors)

    def test_increments_tables_loaded_counter(self):
        ctx = _make_ctx()
        with patch(
            "ingestion.api_football.loads.injuries.fetch_merged_paged",
            return_value=_api_response([{"player": {"id": 1}}]),
        ):
            with patch("ingestion.api_football.loads.injuries.load_json_to_bq"):
                load_injuries(ctx, "BL1", 78, [2024])

        ctx.add_loaded.assert_called_once_with(1)


# ---------------------------------------------------------------------------
# load_coaches
# ---------------------------------------------------------------------------


class TestLoadCoaches:
    def test_calls_api_once_per_team(self):
        ctx = _make_ctx()
        with patch(
            "ingestion.api_football.loads.coaches.fetch_merged_paged",
            return_value=_api_response([]),
        ) as mock_fetch:
            with patch("ingestion.api_football.loads.coaches.load_json_to_bq"):
                load_coaches(ctx, "BL1", {10, 20, 30})

        assert mock_fetch.call_count == 3
        queried_teams = {
            c[0][2]["team"] for c in mock_fetch.call_args_list
        }
        assert queried_teams == {10, 20, 30}

    def test_wraps_each_coach_with_team_id(self):
        ctx = _make_ctx()
        coach_data = {"id": 99, "name": "J. Klopp", "career": []}

        with patch(
            "ingestion.api_football.loads.coaches.fetch_merged_paged",
            return_value=_api_response([coach_data]),
        ):
            with patch(
                "ingestion.api_football.loads.coaches.load_json_to_bq"
            ) as mock_bq:
                load_coaches(ctx, "BL1", {40})

        payload = mock_bq.call_args[0][2]
        assert len(payload["response"]) == 1
        assert payload["response"][0]["team_id"] == 40
        assert payload["response"][0]["coach"]["id"] == 99

    def test_writes_to_correct_table(self):
        ctx = _make_ctx()
        with patch(
            "ingestion.api_football.loads.coaches.fetch_merged_paged",
            return_value=_api_response([{"id": 1}]),
        ):
            with patch(
                "ingestion.api_football.loads.coaches.load_json_to_bq"
            ) as mock_bq:
                load_coaches(ctx, "WC", {1})

        table_name = mock_bq.call_args[0][1]
        assert table_name == "RAW_APIF_WC_COACHES"

    def test_uses_append_mode(self):
        ctx = _make_ctx()
        with patch(
            "ingestion.api_football.loads.coaches.fetch_merged_paged",
            return_value=_api_response([{"id": 1}]),
        ):
            with patch(
                "ingestion.api_football.loads.coaches.load_json_to_bq"
            ) as mock_bq:
                load_coaches(ctx, "BL1", {10})

        kwargs = mock_bq.call_args[1]
        assert kwargs.get("append") is True

    def test_no_op_when_team_ids_empty(self):
        ctx = _make_ctx()
        with patch(
            "ingestion.api_football.loads.coaches.fetch_merged_paged"
        ) as mock_fetch:
            with patch("ingestion.api_football.loads.coaches.load_json_to_bq") as mock_bq:
                load_coaches(ctx, "BL1", set())

        mock_fetch.assert_not_called()
        mock_bq.assert_not_called()

    def test_skips_remaining_teams_when_quota_exhausted(self):
        import ingestion.api_football.quota as quota_mod

        ctx = _make_ctx()
        prev = quota_mod._http_quota_exhausted
        quota_mod._http_quota_exhausted = True
        try:
            with patch(
                "ingestion.api_football.loads.coaches.fetch_merged_paged"
            ) as mock_fetch:
                with patch("ingestion.api_football.loads.coaches.load_json_to_bq"):
                    load_coaches(ctx, "BL1", {10, 20})
        finally:
            quota_mod._http_quota_exhausted = prev

        mock_fetch.assert_not_called()

    def test_team_exception_appended_to_errors_and_continues(self):
        ctx = _make_ctx()
        call_count = 0

        def raise_on_first(path, headers, base_params, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RuntimeError("network error")
            return _api_response([{"id": 5}])

        with patch(
            "ingestion.api_football.loads.coaches.fetch_merged_paged",
            side_effect=raise_on_first,
        ):
            with patch("ingestion.api_football.loads.coaches.load_json_to_bq"):
                load_coaches(ctx, "BL1", {10, 20})

        assert any("coaches" in e and "BL1" in e for e in ctx.errors)

    def test_bq_exception_appended_to_errors(self):
        ctx = _make_ctx()
        with patch(
            "ingestion.api_football.loads.coaches.fetch_merged_paged",
            return_value=_api_response([{"id": 1}]),
        ):
            with patch(
                "ingestion.api_football.loads.coaches.load_json_to_bq",
                side_effect=RuntimeError("BQ write failed"),
            ):
                load_coaches(ctx, "BL1", {10})

        assert any("coaches BQ" in e for e in ctx.errors)

    def test_multiple_coaches_per_team_all_captured(self):
        """A team can have multiple coaches returned (e.g. current + caretakers)."""
        ctx = _make_ctx()
        two_coaches = [{"id": 1, "name": "A"}, {"id": 2, "name": "B"}]

        with patch(
            "ingestion.api_football.loads.coaches.fetch_merged_paged",
            return_value=_api_response(two_coaches),
        ):
            with patch(
                "ingestion.api_football.loads.coaches.load_json_to_bq"
            ) as mock_bq:
                load_coaches(ctx, "BL1", {40})

        payload = mock_bq.call_args[0][2]
        assert len(payload["response"]) == 2

    def test_increments_tables_loaded_counter(self):
        ctx = _make_ctx()
        with patch(
            "ingestion.api_football.loads.coaches.fetch_merged_paged",
            return_value=_api_response([{"id": 1}]),
        ):
            with patch("ingestion.api_football.loads.coaches.load_json_to_bq"):
                load_coaches(ctx, "BL1", {10})

        ctx.add_loaded.assert_called_once_with(1)
