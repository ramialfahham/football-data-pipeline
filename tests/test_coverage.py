"""Tests for coverage.py — RAW_APIF_FIXTURE_COVERAGE read/write helpers.

Pure-function tests cover the mapping constants and covered_for_league().
BigQuery-touching functions (read_coverage, write_coverage) are tested with
a mock client so no live GCP connection is required.
"""

from __future__ import annotations

from unittest.mock import MagicMock, call

import pytest
from google.cloud.exceptions import NotFound

from ingestion.api_football.coverage import (
    ENDPOINT_TO_SHELL_KEY,
    FANOUT_ENDPOINTS,
    SHELL_KEY_TO_ENDPOINT,
    covered_for_league,
    read_coverage,
    write_coverage,
)


# ---------------------------------------------------------------------------
# Mapping constant invariants
# ---------------------------------------------------------------------------


class TestMappingConstants:
    def test_shell_key_to_endpoint_has_all_five_keys(self):
        assert set(SHELL_KEY_TO_ENDPOINT.keys()) == {
            "lineups",
            "events",
            "fx_stats",
            "fx_players",
            "preds",
        }

    def test_endpoint_to_shell_key_is_exact_inverse(self):
        """ENDPOINT_TO_SHELL_KEY must be the perfect inverse of SHELL_KEY_TO_ENDPOINT."""
        for shell_key, endpoint in SHELL_KEY_TO_ENDPOINT.items():
            assert ENDPOINT_TO_SHELL_KEY[endpoint] == shell_key, (
                f"ENDPOINT_TO_SHELL_KEY[{endpoint!r}] should be {shell_key!r}"
            )

    def test_fanout_endpoints_matches_shell_key_values(self):
        """FANOUT_ENDPOINTS must contain exactly the endpoint strings in the mapping."""
        assert set(FANOUT_ENDPOINTS) == set(SHELL_KEY_TO_ENDPOINT.values())

    def test_all_five_fanout_endpoints_present(self):
        assert set(FANOUT_ENDPOINTS) == {
            "LINEUPS",
            "FIXTURE_EVENTS",
            "FIXTURE_STATISTICS",
            "FIXTURE_PLAYERS",
            "PREDICTIONS",
        }


# ---------------------------------------------------------------------------
# covered_for_league — pure dict translation, no BigQuery
# ---------------------------------------------------------------------------


class TestCoveredForLeague:
    def test_empty_coverage_returns_five_empty_sets(self):
        result = covered_for_league({}, "BL1")
        assert set(result.keys()) == {"lineups", "events", "fx_stats", "fx_players", "preds"}
        for key, ids in result.items():
            assert ids == set(), f"expected empty set for shell key {key!r}"

    def test_translates_endpoint_names_to_shell_keys(self):
        all_covered = {
            "BL1": {
                "LINEUPS":            {100, 101},
                "FIXTURE_EVENTS":     {100},
                "FIXTURE_STATISTICS": {100, 101, 102},
                "FIXTURE_PLAYERS":    set(),
                "PREDICTIONS":        {100},
            }
        }
        result = covered_for_league(all_covered, "BL1")
        assert result["lineups"]    == {100, 101}
        assert result["events"]     == {100}
        assert result["fx_stats"]   == {100, 101, 102}
        assert result["fx_players"] == set()
        assert result["preds"]      == {100}

    def test_unknown_league_returns_five_empty_sets(self):
        all_covered = {"BL1": {"LINEUPS": {100}}}
        result = covered_for_league(all_covered, "PL")
        for ids in result.values():
            assert ids == set()

    def test_partial_endpoint_coverage_fills_missing_with_empty_sets(self):
        """A league with only some endpoints covered still returns all five keys."""
        all_covered = {"WC": {"LINEUPS": {200, 201}}}
        result = covered_for_league(all_covered, "WC")
        assert result["lineups"]    == {200, 201}
        assert result["events"]     == set()
        assert result["fx_stats"]   == set()
        assert result["fx_players"] == set()
        assert result["preds"]      == set()

    def test_does_not_mutate_input(self):
        all_covered = {"BL1": {"LINEUPS": {1, 2, 3}}}
        original_set = all_covered["BL1"]["LINEUPS"]
        covered_for_league(all_covered, "BL1")
        # The returned set should be the same object (no copy needed), but the
        # source dict must be unmodified.
        assert all_covered["BL1"]["LINEUPS"] is original_set


# ---------------------------------------------------------------------------
# read_coverage — requires mocked BigQuery client
# ---------------------------------------------------------------------------


class TestReadCoverage:
    def _make_row(self, league_code: str, fixture_id, endpoint: str):
        row = MagicMock()
        row.league_code = league_code
        row.fixture_id  = fixture_id
        row.endpoint    = endpoint
        return row

    def test_returns_empty_dict_when_table_not_found(self):
        client = MagicMock()
        client.get_table.side_effect = NotFound("coverage table not found")
        result = read_coverage(client)
        assert result == {}
        # Should not try to query a non-existent table.
        client.query.assert_not_called()

    def test_groups_rows_by_league_and_endpoint(self):
        client = MagicMock()
        client.get_table.return_value = MagicMock()
        rows = [
            self._make_row("BL1", 100, "LINEUPS"),
            self._make_row("BL1", 101, "LINEUPS"),
            self._make_row("BL1", 100, "FIXTURE_EVENTS"),
            self._make_row("PL",  200, "LINEUPS"),
        ]
        client.query.return_value.result.return_value = rows

        result = read_coverage(client)

        assert result["BL1"]["LINEUPS"]        == {100, 101}
        assert result["BL1"]["FIXTURE_EVENTS"] == {100}
        assert result["PL"]["LINEUPS"]         == {200}

    def test_fixture_ids_are_converted_to_int(self):
        """fixture_id values from BigQuery may arrive as strings — must cast to int."""
        client = MagicMock()
        client.get_table.return_value = MagicMock()
        client.query.return_value.result.return_value = [
            self._make_row("BL1", "12345", "LINEUPS"),
        ]

        result = read_coverage(client)

        assert 12345 in result["BL1"]["LINEUPS"]
        assert all(isinstance(fid, int) for fid in result["BL1"]["LINEUPS"])

    def test_empty_table_returns_empty_dict(self):
        client = MagicMock()
        client.get_table.return_value = MagicMock()
        client.query.return_value.result.return_value = []

        result = read_coverage(client)
        assert result == {}

    def test_returns_plain_dicts_not_defaultdicts(self):
        """Downstream code should not depend on defaultdict's auto-create behaviour."""
        client = MagicMock()
        client.get_table.return_value = MagicMock()
        client.query.return_value.result.return_value = [
            self._make_row("BL1", 1, "LINEUPS"),
        ]
        result = read_coverage(client)
        # Accessing a missing key should raise KeyError, not create a new entry.
        with pytest.raises(KeyError):
            _ = result["NONEXISTENT_LEAGUE"]
        with pytest.raises(KeyError):
            _ = result["BL1"]["NONEXISTENT_ENDPOINT"]


# ---------------------------------------------------------------------------
# write_coverage — requires mocked BigQuery client
# ---------------------------------------------------------------------------


class TestWriteCoverage:
    def test_no_op_when_rows_list_is_empty(self):
        client = MagicMock()
        write_coverage(client, [])
        client.load_table_from_file.assert_not_called()

    def test_calls_load_table_from_file_once(self):
        client = MagicMock()
        job = MagicMock()
        client.load_table_from_file.return_value = job

        write_coverage(client, [
            {"league_code": "BL1", "fixture_id": 100, "endpoint": "LINEUPS"},
            {"league_code": "BL1", "fixture_id": 101, "endpoint": "FIXTURE_EVENTS"},
        ])

        assert client.load_table_from_file.call_count == 1
        job.result.assert_called_once()

    def test_ndjson_contains_all_rows(self):
        """The bytes written to BigQuery must have one JSON object per input row."""
        import io
        import json

        client = MagicMock()
        job = MagicMock()
        client.load_table_from_file.return_value = job

        rows_in = [
            {"league_code": "BL1", "fixture_id": 100, "endpoint": "LINEUPS"},
            {"league_code": "PL",  "fixture_id": 999, "endpoint": "PREDICTIONS"},
        ]
        write_coverage(client, rows_in)

        # Retrieve the BytesIO object passed to load_table_from_file.
        call_args = client.load_table_from_file.call_args
        file_obj = call_args[0][0]
        ndjson_bytes = file_obj.read()
        lines = [l for l in ndjson_bytes.decode("utf-8").strip().split("\n") if l]

        assert len(lines) == 2
        parsed = [json.loads(l) for l in lines]
        league_codes = {r["league_code"] for r in parsed}
        assert league_codes == {"BL1", "PL"}
        # first_fetched_at must be present on every row.
        for row in parsed:
            assert "first_fetched_at" in row
            assert row["fixture_id"] == int(row["fixture_id"])  # stored as int
