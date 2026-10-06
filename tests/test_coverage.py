"""Tests for coverage.py — fanout coverage derived from RAW_APIF_FIXTURE_DETAILS.

Pure-function tests cover the mapping constants and covered_for_league().
read_coverage() is tested with a mock BigQuery client so no live GCP connection
is required. There is no coverage tracking table any more (issue #221): coverage
is derived from the fanout data itself, so there is no write path to test.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest
from google.cloud.exceptions import NotFound

from ingestion.api_football.coverage import (
    ENDPOINT_TO_SHELL_KEY,
    FANOUT_ENDPOINTS,
    NEWER_FORMAT_REFETCH_DELAY,
    SECOND_FETCH_DELAY,
    SHELL_KEY_TO_ENDPOINT,
    STATS_GRACE_DAYS,
    covered_for_league,
    newer_format_refetch_due,
    read_coverage,
    second_fetch_due,
)


# ---------------------------------------------------------------------------
# Mapping constant invariants
# ---------------------------------------------------------------------------


class TestMappingConstants:
    def test_shell_key_to_endpoint_has_four_keys(self):
        assert set(SHELL_KEY_TO_ENDPOINT.keys()) == {
            "lineups",
            "events",
            "fx_stats",
            "fx_players",
        }

    def test_endpoint_to_shell_key_is_exact_inverse(self):
        for shell_key, endpoint in SHELL_KEY_TO_ENDPOINT.items():
            assert ENDPOINT_TO_SHELL_KEY[endpoint] == shell_key, (
                f"ENDPOINT_TO_SHELL_KEY[{endpoint!r}] should be {shell_key!r}"
            )

    def test_fanout_endpoints_matches_shell_key_values(self):
        assert set(FANOUT_ENDPOINTS) == set(SHELL_KEY_TO_ENDPOINT.values())

    def test_no_predictions_endpoint(self):
        # API predictions are not ingested — there must be no PREDICTIONS endpoint.
        assert "PREDICTIONS" not in FANOUT_ENDPOINTS
        assert set(FANOUT_ENDPOINTS) == {
            "LINEUPS",
            "FIXTURE_EVENTS",
            "FIXTURE_STATISTICS",
            "FIXTURE_PLAYERS",
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
    def test_empty_coverage_returns_four_empty_sets(self):
        result = covered_for_league({}, "BL1")
        assert set(result.keys()) == {"lineups", "events", "fx_stats", "fx_players"}
        for key, ids in result.items():
            assert ids == set(), f"expected empty set for shell key {key!r}"

    def test_translates_endpoint_names_to_shell_keys(self):
        all_covered = {
            "BL1": {
                "LINEUPS":            {100: True, 101: True},
                "FIXTURE_EVENTS":     {100: True},
                "FIXTURE_STATISTICS": {100: True, 101: True, 102: True},
                "FIXTURE_PLAYERS":    {},
            }
        }
        result = covered_for_league(all_covered, "BL1")
        assert result["lineups"]    == {100, 101}
        assert result["events"]     == {100}
        assert result["fx_stats"]   == {100, 101, 102}
        assert result["fx_players"] == set()

    def test_unknown_league_returns_four_empty_sets(self):
        all_covered = {"BL1": {"LINEUPS": {100: True}}}
        result = covered_for_league(all_covered, "PL")
        assert set(result.keys()) == {"lineups", "events", "fx_stats", "fx_players"}
        for ids in result.values():
            assert ids == set()

    def test_partial_endpoint_coverage_fills_missing_with_empty_sets(self):
        all_covered = {"WC": {"LINEUPS": {200: True, 201: True}}}
        result = covered_for_league(all_covered, "WC")
        assert result["lineups"]    == {200, 201}
        assert result["events"]     == set()
        assert result["fx_stats"]   == set()
        assert result["fx_players"] == set()

    def test_does_not_mutate_input(self):
        all_covered = {"BL1": {"LINEUPS": {1: True, 2: True, 3: True}}}
        original_dict = all_covered["BL1"]["LINEUPS"]
        covered_for_league(all_covered, "BL1")
        assert all_covered["BL1"]["LINEUPS"] is original_dict

    # --- has_data=True: always skip ---

    def test_has_data_true_always_skipped(self):
        today = _today()
        all_covered = {"BL1": {"FIXTURE_STATISTICS": {500: True}}}
        kickoff_by_id = {500: today}  # would be within grace period, but has_data=True
        result = covered_for_league(all_covered, "BL1", kickoff_by_id=kickoff_by_id)
        assert 500 in result["fx_stats"]

    # --- has_data=False + FIXTURE_STATISTICS: grace-period logic ---

    def test_stats_empty_within_grace_retried(self):
        today = _today()
        recent_kickoff = today - timedelta(days=STATS_GRACE_DAYS - 1)
        all_covered = {"BL1": {"FIXTURE_STATISTICS": {42: False}}}
        kickoff_by_id = {42: recent_kickoff}
        result = covered_for_league(all_covered, "BL1", kickoff_by_id=kickoff_by_id)
        assert 42 not in result["fx_stats"], (
            "Fixture within grace period must be retried (not in skip set)"
        )

    def test_stats_empty_exactly_at_grace_boundary_skipped(self):
        today = _today()
        boundary_kickoff = today - timedelta(days=STATS_GRACE_DAYS)
        all_covered = {"BL1": {"FIXTURE_STATISTICS": {43: False}}}
        kickoff_by_id = {43: boundary_kickoff}
        result = covered_for_league(all_covered, "BL1", kickoff_by_id=kickoff_by_id)
        assert 43 in result["fx_stats"], (
            "Fixture at grace boundary must be skipped (grace period elapsed)"
        )

    def test_stats_empty_after_grace_skipped(self):
        today = _today()
        old_kickoff = today - timedelta(days=STATS_GRACE_DAYS + 5)
        all_covered = {"BL1": {"FIXTURE_STATISTICS": {44: False}}}
        kickoff_by_id = {44: old_kickoff}
        result = covered_for_league(all_covered, "BL1", kickoff_by_id=kickoff_by_id)
        assert 44 in result["fx_stats"]

    def test_stats_empty_no_kickoff_info_skipped_conservatively(self):
        all_covered = {"BL1": {"FIXTURE_STATISTICS": {45: False}}}
        kickoff_by_id = {}  # fixture 45 not in kickoff map
        result = covered_for_league(all_covered, "BL1", kickoff_by_id=kickoff_by_id)
        assert 45 in result["fx_stats"]

    def test_stats_empty_no_kickoff_by_id_skipped_conservatively(self):
        all_covered = {"BL1": {"FIXTURE_STATISTICS": {46: False}}}
        result = covered_for_league(all_covered, "BL1")  # no kickoff_by_id
        assert 46 in result["fx_stats"]

    # --- has_data=False + non-statistics endpoints: always skip ---

    def test_non_stats_empty_response_skipped_conservatively(self):
        """has_data=False on LINEUPS/EVENTS/PLAYERS → always skip.

        The derive marks LINEUPS and EVENTS True whenever the fixture was fetched;
        PLAYERS is False only while its second fetch is due, which the fixture-details
        step makes in every competition, so it must not switch an idle competition to
        full mode.
        """
        today = _today()
        recent = today - timedelta(days=1)
        all_covered = {
            "BL1": {
                "LINEUPS":        {10: False},
                "FIXTURE_EVENTS": {11: False},
                "FIXTURE_PLAYERS": {12: False},
            }
        }
        kickoff_by_id = {10: recent, 11: recent, 12: recent}
        result = covered_for_league(all_covered, "BL1", kickoff_by_id=kickoff_by_id)
        assert 10 in result["lineups"]
        assert 11 in result["events"]
        assert 12 in result["fx_players"]

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
        assert 100 in result["fx_stats"]     # has data → skip
        assert 101 not in result["fx_stats"]  # within grace → retry
        assert 102 in result["fx_stats"]     # grace elapsed → skip


# ---------------------------------------------------------------------------
# read_coverage — derives coverage from RAW_APIF_FIXTURE_DETAILS (mocked client)
#
# The query returns one row per (league_code, fixture_id) with a has_statistics
# flag. The four endpoints are reconstructed in Python: statistics reflects the
# flag; lineups/events/players are True for any fetched fixture.
# ---------------------------------------------------------------------------


class TestReadCoverage:
    def _row(
        self,
        league_code: str,
        fixture_id,
        has_statistics: bool,
        latest_fetch: datetime | None = None,
        kickoff: datetime | None = None,
        latest_in_newer_format: bool = False,
    ):
        row = MagicMock()
        row.league_code = league_code
        row.fixture_id = fixture_id
        row.has_statistics = has_statistics
        row.latest_fetch = latest_fetch
        row.kickoff = kickoff
        row.latest_in_newer_format = latest_in_newer_format
        return row

    def _read(self, *rows):
        client = MagicMock()
        client.get_table.return_value = MagicMock()
        client.query.return_value.result.return_value = list(rows)
        return read_coverage(client)

    def test_players_not_covered_while_second_fetch_is_due(self):
        kickoff = datetime.now(timezone.utc) - timedelta(days=10)
        result = self._read(
            self._row("WC", 1, True, latest_fetch=kickoff + timedelta(hours=8), kickoff=kickoff),
        )
        assert result["WC"]["FIXTURE_PLAYERS"][1] is False
        assert result["WC"]["FIXTURE_STATISTICS"][1] is True
        assert result["WC"]["LINEUPS"][1] is True

    def test_players_covered_once_fetched_late_enough(self):
        kickoff = datetime.now(timezone.utc) - timedelta(days=10)
        result = self._read(
            self._row("WC", 1, True, latest_fetch=kickoff + SECOND_FETCH_DELAY, kickoff=kickoff),
        )
        assert result["WC"]["FIXTURE_PLAYERS"][1] is True

    def test_players_not_covered_while_newer_format_refetch_is_due(self):
        kickoff = datetime.now(timezone.utc) - timedelta(days=20)
        result = self._read(
            self._row(
                "WC", 1, True, latest_fetch=kickoff + timedelta(days=4), kickoff=kickoff,
                latest_in_newer_format=True,
            ),
        )
        assert result["WC"]["FIXTURE_PLAYERS"][1] is False
        assert result["WC"]["FIXTURE_STATISTICS"][1] is True

    def test_players_covered_when_latest_fetch_is_complete(self):
        kickoff = datetime.now(timezone.utc) - timedelta(days=20)
        result = self._read(
            self._row("WC", 1, True, latest_fetch=kickoff + timedelta(days=4), kickoff=kickoff),
        )
        assert result["WC"]["FIXTURE_PLAYERS"][1] is True

    def test_players_covered_before_the_delay_has_passed(self):
        kickoff = datetime.now(timezone.utc) - timedelta(days=1)
        result = self._read(
            self._row("WC", 1, True, latest_fetch=kickoff + timedelta(hours=8), kickoff=kickoff),
        )
        assert result["WC"]["FIXTURE_PLAYERS"][1] is True

    def test_returns_empty_dict_when_table_not_found(self):
        client = MagicMock()
        client.get_table.side_effect = NotFound("fixture details table not found")
        result = read_coverage(client)
        assert result == {}
        client.query.assert_not_called()

    def test_derives_all_four_endpoints_per_fixture(self):
        client = MagicMock()
        client.get_table.return_value = MagicMock()
        client.query.return_value.result.return_value = [
            self._row("BL1", 100, has_statistics=True),
        ]
        result = read_coverage(client)
        # statistics reflects the flag; the other three are True for a fetched fixture.
        assert result["BL1"]["FIXTURE_STATISTICS"][100] is True
        assert result["BL1"]["LINEUPS"][100] is True
        assert result["BL1"]["FIXTURE_EVENTS"][100] is True
        assert result["BL1"]["FIXTURE_PLAYERS"][100] is True

    def test_empty_statistics_marks_only_statistics_false(self):
        client = MagicMock()
        client.get_table.return_value = MagicMock()
        client.query.return_value.result.return_value = [
            self._row("BL1", 200, has_statistics=False),
        ]
        result = read_coverage(client)
        # The fixture was fetched (row exists) but its statistics array was empty.
        assert result["BL1"]["FIXTURE_STATISTICS"][200] is False
        assert result["BL1"]["LINEUPS"][200] is True
        assert result["BL1"]["FIXTURE_EVENTS"][200] is True
        assert result["BL1"]["FIXTURE_PLAYERS"][200] is True

    def test_no_predictions_endpoint_in_result(self):
        client = MagicMock()
        client.get_table.return_value = MagicMock()
        client.query.return_value.result.return_value = [
            self._row("BL1", 1, has_statistics=True),
        ]
        result = read_coverage(client)
        assert "PREDICTIONS" not in result["BL1"]
        assert set(result["BL1"].keys()) == {
            "LINEUPS", "FIXTURE_EVENTS", "FIXTURE_STATISTICS", "FIXTURE_PLAYERS"
        }

    def test_groups_multiple_leagues(self):
        client = MagicMock()
        client.get_table.return_value = MagicMock()
        client.query.return_value.result.return_value = [
            self._row("BL1", 100, has_statistics=True),
            self._row("PL", 300, has_statistics=False),
        ]
        result = read_coverage(client)
        assert result["BL1"]["FIXTURE_STATISTICS"][100] is True
        assert result["PL"]["FIXTURE_STATISTICS"][300] is False

    def test_fixture_ids_are_converted_to_int(self):
        client = MagicMock()
        client.get_table.return_value = MagicMock()
        client.query.return_value.result.return_value = [
            self._row("BL1", "12345", has_statistics=True),
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
        client = MagicMock()
        client.get_table.return_value = MagicMock()
        client.query.return_value.result.return_value = [
            self._row("BL1", 1, has_statistics=True),
        ]
        result = read_coverage(client)
        with pytest.raises(KeyError):
            _ = result["NONEXISTENT_LEAGUE"]
        with pytest.raises(KeyError):
            _ = result["BL1"]["NONEXISTENT_ENDPOINT"]


# ---------------------------------------------------------------------------
# second_fetch_due — the player stats' second fetch, decided on 72 hours from kickoff
# ---------------------------------------------------------------------------


class TestSecondFetchDue:
    KICKOFF = datetime(2026, 10, 1, 19, 0, tzinfo=timezone.utc)
    COMPLETE_FROM = KICKOFF + SECOND_FETCH_DELAY

    def test_early_fetch_is_due_once_the_delay_has_passed(self):
        early = self.KICKOFF + timedelta(hours=9)
        assert second_fetch_due(early, self.KICKOFF, self.COMPLETE_FROM) is True

    def test_early_fetch_is_not_due_before_the_delay(self):
        early = self.KICKOFF + timedelta(hours=9)
        now = self.COMPLETE_FROM - timedelta(minutes=1)
        assert second_fetch_due(early, self.KICKOFF, now) is False

    def test_evening_match_is_not_due_on_the_third_calendar_day(self):
        """Three calendar days after a 19:00 kickoff, the 04:00 run is only 57 hours later."""
        early = self.KICKOFF + timedelta(hours=9)
        third_day_run = datetime(2026, 10, 4, 4, 0, tzinfo=timezone.utc)
        assert second_fetch_due(early, self.KICKOFF, third_day_run) is False

    def test_fetch_made_at_the_delay_is_never_due(self):
        later = self.COMPLETE_FROM + timedelta(days=30)
        assert second_fetch_due(self.COMPLETE_FROM, self.KICKOFF, later) is False

    def test_unknown_kickoff_or_fetch_is_never_due(self):
        assert second_fetch_due(None, self.KICKOFF, self.COMPLETE_FROM) is False
        assert second_fetch_due(self.KICKOFF, None, self.COMPLETE_FROM) is False


# ---------------------------------------------------------------------------
# newer_format_refetch_due — a latest fetch in the newer format, fetched again 14 days from kickoff
# ---------------------------------------------------------------------------


class TestNewerFormatRefetchDue:
    KICKOFF = datetime(2026, 10, 1, 19, 0, tzinfo=timezone.utc)
    REFETCH_FROM = KICKOFF + NEWER_FORMAT_REFETCH_DELAY
    THIRD_DAY_FETCH = KICKOFF + SECOND_FETCH_DELAY

    def test_newer_format_fetch_is_due_once_the_delay_has_passed(self):
        assert newer_format_refetch_due(self.THIRD_DAY_FETCH, self.KICKOFF, True, self.REFETCH_FROM) is True

    def test_newer_format_fetch_is_not_due_before_the_delay(self):
        now = self.REFETCH_FROM - timedelta(minutes=1)
        assert newer_format_refetch_due(self.THIRD_DAY_FETCH, self.KICKOFF, True, now) is False

    def test_complete_format_fetch_is_never_due(self):
        later = self.REFETCH_FROM + timedelta(days=30)
        assert newer_format_refetch_due(self.THIRD_DAY_FETCH, self.KICKOFF, False, later) is False

    def test_fetch_made_at_the_delay_is_never_due_again(self):
        later = self.REFETCH_FROM + timedelta(days=30)
        assert newer_format_refetch_due(self.REFETCH_FROM, self.KICKOFF, True, later) is False

    def test_unknown_kickoff_or_fetch_is_never_due(self):
        assert newer_format_refetch_due(None, self.KICKOFF, True, self.REFETCH_FROM) is False
        assert newer_format_refetch_due(self.THIRD_DAY_FETCH, None, True, self.REFETCH_FROM) is False
