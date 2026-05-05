"""Tests for fixture_scheduling.py — coverage flags and the fanout gate.

The coverage flag gate (_fixture_needs_any_endpoint) was the root cause of the
WC statistics bug (PR #40): the API reports fixture_statistics=false for WC 2026
(upcoming reference season), which caused all 2022/2018 finished fixtures to be
skipped entirely. The fix: finished fixtures always get a stats attempt regardless
of the coverage flag.

These tests pin that fix as a regression test.
"""

import pytest
from ingestion.api_football.fixture_scheduling import _coverage_for_season
from ingestion.api_football.loads.fanout import (
    _fixture_needs_any_endpoint,
    _finished_fixture_ids,
    _FANOUT_ENTITY_KEYS,
)


# ---------------------------------------------------------------------------
# _coverage_for_season — reads /leagues API response
# ---------------------------------------------------------------------------

def _leagues_envelope(season: int, stats: bool = True, lineups: bool = True) -> dict:
    return {
        "response": [{
            "seasons": [{
                "year": season,
                "coverage": {
                    "standings": True,
                    "injuries": True,
                    "predictions": True,
                    "fixtures": {
                        "events": True,
                        "lineups": lineups,
                        "statistics_fixtures": stats,
                        "statistics_players": True,
                    },
                },
            }]
        }]
    }


class TestCoverageForSeason:
    def test_all_flags_true_when_api_says_true(self):
        cov = _coverage_for_season(_leagues_envelope(2024, stats=True, lineups=True), 2024)
        assert cov["fixture_statistics"] is True
        assert cov["fixture_lineups"] is True

    def test_stats_false_when_api_says_false(self):
        cov = _coverage_for_season(_leagues_envelope(2024, stats=False), 2024)
        assert cov["fixture_statistics"] is False

    def test_missing_season_defaults_to_true(self):
        # Season not in envelope → default True (safer to attempt)
        cov = _coverage_for_season(_leagues_envelope(2024), 2099)
        assert cov["fixture_statistics"] is True

    def test_empty_envelope_defaults_all_true(self):
        cov = _coverage_for_season({}, 2024)
        for key in ("fixture_statistics", "fixture_lineups", "fixture_events",
                    "fixture_players", "predictions"):
            assert cov[key] is True, f"{key} should default to True"


# ---------------------------------------------------------------------------
# _finished_fixture_ids — status parsing
# ---------------------------------------------------------------------------

class TestFinishedFixtureIds:
    def _row(self, fid, status):
        return {"fixture": {"id": fid, "status": {"short": status}}}

    def test_ft_included(self):
        result = _finished_fixture_ids([self._row(1, "FT")])
        assert 1 in result

    def test_aet_included(self):
        result = _finished_fixture_ids([self._row(2, "AET")])
        assert 2 in result

    def test_pen_included(self):
        result = _finished_fixture_ids([self._row(3, "PEN")])
        assert 3 in result

    def test_ns_not_included(self):
        result = _finished_fixture_ids([self._row(4, "NS")])
        assert 4 not in result

    def test_1h_not_included(self):
        result = _finished_fixture_ids([self._row(5, "1H")])
        assert 5 not in result

    def test_empty_input(self):
        assert _finished_fixture_ids([]) == set()


# ---------------------------------------------------------------------------
# _fixture_needs_any_endpoint — the coverage flag gate (PR #40 regression)
# ---------------------------------------------------------------------------

def _covered_nothing() -> dict[str, set[int]]:
    return {key: set() for key, _, _ in _FANOUT_ENTITY_KEYS}


def _covered_all(fixture_id: int) -> dict[str, set[int]]:
    return {key: {fixture_id} for key, _, _ in _FANOUT_ENTITY_KEYS}


class TestFixtureNeedsAnyEndpoint:
    def test_uncovered_fixture_needs_fetch(self):
        cov = {"fixture_lineups": True, "fixture_events": True, "fixture_statistics": True,
               "fixture_players": True, "predictions": True}
        assert _fixture_needs_any_endpoint(1, _covered_nothing(), cov, finished_fixture_ids=set())

    def test_fully_covered_fixture_skipped(self):
        cov = {"fixture_lineups": True, "fixture_events": True, "fixture_statistics": True,
               "fixture_players": True, "predictions": True}
        assert not _fixture_needs_any_endpoint(1, _covered_all(1), cov, finished_fixture_ids=set())

    def test_wc2026_regression_finished_fixture_needs_stats(self):
        # WC 2026 case: reference season is upcoming → stats flag is False.
        # A 2022 World Cup finished fixture must still enter the fanout loop for stats.
        cov = {
            "fixture_lineups": True,
            "fixture_events": True,
            "fixture_statistics": False,   # API says unsupported for WC 2026 reference season
            "fixture_players": True,
            "predictions": True,
        }
        covered = _covered_all(100)
        # Everything covered except stats (which isn't in covered_all because stats=False
        # means it was never fetched). Simulate: lineups/events/players/preds all covered,
        # fx_stats not covered.
        covered["fx_stats"] = set()

        finished = {100}  # fixture 100 is FT
        assert _fixture_needs_any_endpoint(100, covered, cov, finished_fixture_ids=finished), (
            "Finished fixture must need stats fetch even when coverage flag is False"
        )

    def test_wc2026_regression_upcoming_fixture_respects_stats_flag(self):
        # Upcoming fixture (not in finished_fixture_ids) should respect the flag.
        cov = {
            "fixture_lineups": True,
            "fixture_events": True,
            "fixture_statistics": False,
            "fixture_players": True,
            "predictions": True,
        }
        covered = _covered_all(200)
        covered["fx_stats"] = set()  # stats not covered, but fixture is upcoming

        finished = set()  # fixture 200 is NOT finished
        # Since stats flag is False and fixture is not finished, stats endpoint is disabled.
        # If lineups/events/players/preds are all covered, the fixture doesn't need a fetch.
        assert not _fixture_needs_any_endpoint(200, covered, cov, finished_fixture_ids=finished)

    def test_endpoint_disabled_by_coverage_does_not_block_completion(self):
        # predictions=False: a fixture that has everything else covered is considered complete.
        cov = {
            "fixture_lineups": True,
            "fixture_events": True,
            "fixture_statistics": True,
            "fixture_players": True,
            "predictions": False,   # competition doesn't support predictions
        }
        covered = {key: {300} for key, _, _ in _FANOUT_ENTITY_KEYS}
        covered["preds"] = set()  # predictions not covered, but flag is False

        assert not _fixture_needs_any_endpoint(300, covered, cov, finished_fixture_ids=set())

    def test_partial_coverage_still_needs_fetch(self):
        # lineups covered, but events not → still needs a fetch
        cov = {"fixture_lineups": True, "fixture_events": True, "fixture_statistics": True,
               "fixture_players": True, "predictions": True}
        covered = _covered_nothing()
        covered["lineups"] = {50}  # only lineups covered

        assert _fixture_needs_any_endpoint(50, covered, cov, finished_fixture_ids=set())
