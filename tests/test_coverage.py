"""Tests for coverage.py — RAW_APIF_FIXTURE_COVERAGE read/write helpers.

Pure-function tests cover the mapping constants and covered_for_league().
BigQuery-touching functions (read_coverage, write_coverage) are tested with
a mock client so no live GCP connection is required.
"""

from __future__ import annotations

from datetime import date, timedelta
from unittest.mock import MagicMock, call

import pytest
from google.cloud.exceptions import NotFound

from ingestion.api_football.coverage import (
    ENDPOINT_TO_SHELL_KEY,
    FANOUT_ENDPOINTS,
    SHELL_KEY_TO_ENDPOINT,
    STATS_GRACE_DAYS,
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
# covered_for_league — pure dict translation with grace-period logic
#
# all_covered format:  {league_code: {endpoint: {fixture_id: has_data (bool)}}}
# Result format:       {shell_key: set[fixture_id]}  (IDs that should be skipped)
# ---------------------------------------------------------------------------


def _today() -> date:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).date()


class TestCoveredForLeague:
    def test_empty_coverage_returns_five_empty_sets(self):
        result = covered_for_league({}, "BL1")
        assert set(result.keys()) == {"lineups", "events", "fx_stats", "fx_players", "preds"}
        for key, ids in result.items():
            assert ids == set(), f"expected empty set for shell key {key!r}"

    def test_translates_endpoint_names_to_shell_keys(self):
        all_covered = {
            "BL1": {
                "LINEUPS":            {100: True, 101: True},
                "FIXTURE_EVENTS":     {100: True},
                "FIXTURE_STATISTICS": {100: True, 101: True, 102: True},
                "FIXTURE_PLAYERS":    {},
                "PREDICTIONS":        {100: True},
            }
        }
        result = covered_for_league(all_covered, "BL1")
        assert result["lineups"]    == {100, 101}
        assert result["events"]     == {100}
        assert result["fx_stats"]   == {100, 101, 102}
        assert result["fx_players"] == set()
        assert result["preds"]      == {100}

    def test_unknown_league_returns_five_empty_sets(self):
        all_covered = {"BL1": {"LINEUPS": {100: True}}}
        result = covered_for_league(all_covered, "PL")
        for ids in result.values():
            assert ids == set()

    def test_partial_endpoint_coverage_fills_missing_with_empty_sets(self):
        """A league with only some endpoints covered still returns all five keys."""
        all_covered = {"WC": {"LINEUPS": {200: True, 201: True}}}
        result = covered_for_league(all_covered, "WC")
        assert result["lineups"]    == {200, 201}
        assert result["events"]     == set()
        assert result["fx_stats"]   == set()
        assert result["fx_players"] == set()
        assert result["preds"]      == set()

    def test_does_not_mutate_input(self):
        all_covered = {"BL1": {"LINEUPS": {1: True, 2: True, 3: True}}}
        original_dict = all_covered["BL1"]["LINEUPS"]
        covered_for_league(all_covered, "BL1")
        assert all_covered["BL1"]["LINEUPS"] is original_dict

    # --- has_data=True: always skip ---

    def test_has_data_true_always_skipped(self):
        """has_data=True for FIXTURE_STATISTICS means data was received — never retry."""
        today = _today()
        all_covered = {"BL1": {"FIXTURE_STATISTICS": {500: True}}}
        kickoff_by_id = {500: today}  # would be within grace period, but has_data=True
        result = covered_for_league(all_covered, "BL1", kickoff_by_id=kickoff_by_id)
        assert 500 in result["fx_stats"]

    # --- has_data=False + FIXTURE_STATISTICS: grace-period logic ---

    def test_stats_empty_within_grace_retried(self):
        """has_data=False for FIXTURE_STATISTICS within grace period → NOT in skip set."""
        today = _today()
        recent_kickoff = today - timedelta(days=STATS_GRACE_DAYS - 1)
        all_covered = {"BL1": {"FIXTURE_STATISTICS": {42: False}}}
        kickoff_by_id = {42: recent_kickoff}
        result = covered_for_league(all_covered, "BL1", kickoff_by_id=kickoff_by_id)
        assert 42 not in result["fx_stats"], (
            "Fixture within grace period must be retried (not in skip set)"
        )

    def test_stats_empty_exactly_at_grace_boundary_skipped(self):
        """has_data=False exactly STATS_GRACE_DAYS ago → grace elapsed → skip."""
        today = _today()
        boundary_kickoff = today - timedelta(days=STATS_GRACE_DAYS)
        all_covered = {"BL1": {"FIXTURE_STATISTICS": {43: False}}}
        kickoff_by_id = {43: boundary_kickoff}
        result = covered_for_league(all_covered, "BL1", kickoff_by_id=kickoff_by_id)
        assert 43 in result["fx_stats"], (
            "Fixture at grace boundary must be skipped (grace period elapsed)"
        )

    def test_stats_empty_after_grace_skipped(self):
        """has_data=False after grace period → stop retrying."""
        today = _today()
        old_kickoff = today - timedelta(days=STATS_GRACE_DAYS + 5)
        all_covered = {"BL1": {"FIXTURE_STATISTICS": {44: False}}}
        kickoff_by_id = {44: old_kickoff}
        result = covered_for_league(all_covered, "BL1", kickoff_by_id=kickoff_by_id)
        assert 44 in result["fx_stats"]

    def test_stats_empty_no_kickoff_info_skipped_conservatively(self):
        """has_data=False for FIXTURE_STATISTICS with unknown kickoff → skip (conservative)."""
        all_covered = {"BL1": {"FIXTURE_STATISTICS": {45: False}}}
        kickoff_by_id = {}  # fixture 45 not in kickoff map
        result = covered_for_league(all_covered, "BL1", kickoff_by_id=kickoff_by_id)
        assert 45 in result["fx_stats"]

    def test_stats_empty_no_kickoff_by_id_skipped_conservatively(self):
        """When kickoff_by_id is not passed at all, has_data=False → skip conservatively."""
        all_covered = {"BL1": {"FIXTURE_STATISTICS": {46: False}}}
        result = covered_for_league(all_covered, "BL1")  # no kickoff_by_id
        assert 46 in result["fx_stats"]

    # --- has_data=False + non-statistics endpoints: always skip ---

    def test_non_stats_empty_response_skipped_conservatively(self):
        """has_data=False on LINEUPS/EVENTS/PLAYERS/PREDICTIONS → always skip.

        These endpoints never wrote has_data=False under the old code. The
        conservative skip ensures that if an unexpected False ever appears, it
        does not cause infinite re-fetching.
        """
        today = _today()
        recent = today - timedelta(days=1)
        all_covered = {
            "BL1": {
                "LINEUPS":        {10: False},
                "FIXTURE_EVENTS": {11: False},
                "FIXTURE_PLAYERS": {12: False},
                "PREDICTIONS":    {13: False},
            }
        }
        kickoff_by_id = {10: recent, 11: recent, 12: recent, 13: recent}
        result = covered_for_league(all_covered, "BL1", kickoff_by_id=kickoff_by_id)
        assert 10 in result["lineups"]
        assert 11 in result["events"]
        assert 12 in result["fx_players"]
        assert 13 in result["preds"]

    # --- mixed has_data in same endpoint ---

    def test_mix_of_covered_and_retryable_in_same_endpoint(self):
        today = _today()
        recent = today - timedelta(days=2)
        old = today - timedelta(days=STATS_GRACE_DAYS + 1)
        all_covered = {
            "BL1": {
                "FIXTURE_STATISTICS": {
                    100: True,   # has data → skip
                    101: False,  # within grace, recent kickoff → retry
                    102: False,  # outside grace, old kickoff → skip
                }
            }
        }
        kickoff_by_id = {100: recent, 101: recent, 102: old}
        result = covered_for_league(all_covered, "BL1", kickoff_by_id=kickoff_by_id)
        assert 100 in result["fx_stats"]    # has data → skip
        assert 101 not in result["fx_stats"] # within grace → retry
        assert 102 in result["fx_stats"]    # grace elapsed → skip


# ---------------------------------------------------------------------------
# read_coverage — requires mocked BigQuery client
# ---------------------------------------------------------------------------


class TestReadCoverage:
    def _make_row(self, league_code: str, fixture_id, endpoint: str, has_data: bool = True):
        row = MagicMock()
        row.league_code = league_code
        row.fixture_id  = fixture_id
        row.endpoint    = endpoint
        row.has_data    = has_data
        return row

    def test_returns_empty_dict_when_table_not_found(self):
        client = MagicMock()
        client.get_table.side_effect = NotFound("coverage table not found")
        result = read_coverage(client)
        assert result == {}
        # Should not try to query a non-existent table.
        client.query.assert_not_called()

    def test_groups_rows_by_league_and_endpoint_with_has_data(self):
        client = MagicMock()
        client.get_table.return_value = MagicMock()
        rows = [
            self._make_row("BL1", 100, "LINEUPS", has_data=True),
            self._make_row("BL1", 101, "LINEUPS", has_data=True),
            self._make_row("BL1", 100, "FIXTURE_EVENTS", has_data=True),
            self._make_row("BL1", 200, "FIXTURE_STATISTICS", has_data=False),
            self._make_row("PL",  300, "LINEUPS", has_data=True),
        ]
        client.query.return_value.result.return_value = rows

        result = read_coverage(client)

        assert result["BL1"]["LINEUPS"][100]              is True
        assert result["BL1"]["LINEUPS"][101]              is True
        assert result["BL1"]["FIXTURE_EVENTS"][100]       is True
        assert result["BL1"]["FIXTURE_STATISTICS"][200]   is False
        assert result["PL"]["LINEUPS"][300]               is True

    def test_fixture_ids_are_converted_to_int(self):
        """fixture_id values from BigQuery may arrive as strings — must cast to int."""
        client = MagicMock()
        client.get_table.return_value = MagicMock()
        client.query.return_value.result.return_value = [
            self._make_row("BL1", "12345", "LINEUPS", has_data=True),
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
            self._make_row("BL1", 1, "LINEUPS", has_data=True),
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

    def test_ndjson_contains_all_rows_with_has_data(self):
        """The bytes written to BigQuery must have one JSON object per input row
        including has_data, defaulting to True when not provided."""
        import io
        import json

        client = MagicMock()
        job = MagicMock()
        client.load_table_from_file.return_value = job

        rows_in = [
            {"league_code": "BL1", "fixture_id": 100, "endpoint": "LINEUPS"},
            {"league_code": "BL1", "fixture_id": 200, "endpoint": "FIXTURE_STATISTICS", "has_data": False},
            {"league_code": "PL",  "fixture_id": 999, "endpoint": "PREDICTIONS", "has_data": True},
        ]
        write_coverage(client, rows_in)

        call_args = client.load_table_from_file.call_args
        file_obj = call_args[0][0]
        ndjson_bytes = file_obj.read()
        lines = [l for l in ndjson_bytes.decode("utf-8").strip().split("\n") if l]

        assert len(lines) == 3
        parsed = {(r["league_code"], r["fixture_id"]): r for r in (json.loads(l) for l in lines)}

        # Default True when has_data not supplied.
        assert parsed[("BL1", 100)]["has_data"] is True
        # Explicit False preserved.
        assert parsed[("BL1", 200)]["has_data"] is False
        # Explicit True preserved.
        assert parsed[("PL", 999)]["has_data"] is True

        # first_fetched_at must be present on every row.
        for row in parsed.values():
            assert "first_fetched_at" in row
            assert row["fixture_id"] == int(row["fixture_id"])

    def test_has_data_defaults_to_true_when_absent(self):
        """Callers that omit has_data (e.g. populate_coverage_table.py) get True."""
        import json

        client = MagicMock()
        client.load_table_from_file.return_value = MagicMock()

        write_coverage(client, [
            {"league_code": "WC", "fixture_id": 1, "endpoint": "LINEUPS"},
        ])

        file_obj = client.load_table_from_file.call_args[0][0]
        row = json.loads(file_obj.read().decode("utf-8").strip())
        assert row["has_data"] is True
