"""Tests for fixture_scheduling.py — coverage flags and the fanout gate."""

import pytest
from datetime import date
from ingestion.api_football.fixture_scheduling import (
    _coverage_for_season,
    _FANOUT_ENTITY_KEYS,
    _fixture_needs_any_endpoint,
    CompetitionFanoutInput,
    build_global_fanout_queue,
)
from ingestion.api_football.loads.batch_fixtures import _finished_fixture_ids


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
# _fixture_needs_any_endpoint — the coverage flag gate
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

    def test_finished_fixture_needs_stats_regardless_of_coverage_flag(self):
        # When the reference season is upcoming (e.g. any future tournament), the API
        # reports fixture_statistics=false. Finished fixtures from prior seasons must
        # still enter the fanout loop for stats — the flag reflects the reference season,
        # not whether historical data exists.
        cov = {
            "fixture_lineups": True,
            "fixture_events": True,
            "fixture_statistics": False,
            "fixture_players": True,
            "predictions": True,
        }
        covered = _covered_all(100)
        covered["fx_stats"] = set()  # stats not yet fetched

        finished = {100}
        assert _fixture_needs_any_endpoint(100, covered, cov, finished_fixture_ids=finished), (
            "Finished fixture must need stats fetch even when coverage flag is False"
        )

    def test_upcoming_fixture_respects_stats_coverage_flag(self):
        # An unplayed fixture should respect the coverage flag — do not spend quota
        # on an endpoint the competition genuinely does not support.
        cov = {
            "fixture_lineups": True,
            "fixture_events": True,
            "fixture_statistics": False,
            "fixture_players": True,
            "predictions": True,
        }
        covered = _covered_all(200)
        covered["fx_stats"] = set()  # stats not covered, but fixture is not finished

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


# ---------------------------------------------------------------------------
# build_global_fanout_queue — two-tier priority ordering
# ---------------------------------------------------------------------------

def _all_cov() -> dict[str, bool]:
    return {
        "fixture_lineups": True, "fixture_events": True, "fixture_statistics": True,
        "fixture_players": True, "predictions": True,
    }


def _make_input(
    league_code: str,
    fixture_ids: set[int],
    covered_ids: set[int],
    finished_ids: set[int],
    kickoff_by_id: dict[int, date] | None = None,
) -> CompetitionFanoutInput:
    covered = {key: set(covered_ids) for key, _, _ in _FANOUT_ENTITY_KEYS}
    return CompetitionFanoutInput(
        league_code=league_code,
        fixture_ids=fixture_ids,
        covered=covered,
        cov=_all_cov(),
        kickoff_by_id=kickoff_by_id or {},
        finished_fixture_ids=finished_ids,
    )


class TestBuildGlobalFanoutQueue:
    def test_empty_inputs_returns_empty(self):
        assert build_global_fanout_queue([]) == []

    def test_fully_covered_competition_produces_nothing(self):
        inp = _make_input("BL1", {1, 2}, covered_ids={1, 2}, finished_ids={1, 2})
        assert build_global_fanout_queue([inp]) == []

    def test_finished_fixtures_before_upcoming(self):
        # Fixture 10 = finished, missing. Fixture 20 = upcoming, missing.
        # Finished must appear before upcoming in queue regardless of kickoff date.
        inp = _make_input(
            "BL1",
            fixture_ids={10, 20},
            covered_ids=set(),
            finished_ids={10},
            kickoff_by_id={
                10: date(2025, 3, 1),  # older kickoff but finished
                20: date(2025, 2, 1),  # newer kickoff but upcoming
            },
        )
        queue = build_global_fanout_queue([inp])
        lc_fids = [(lc, fid) for lc, fid in queue]
        finished_entry = ("BL1", 10)
        upcoming_entry = ("BL1", 20)
        assert finished_entry in lc_fids
        assert upcoming_entry in lc_fids
        assert lc_fids.index(finished_entry) < lc_fids.index(upcoming_entry)

    def test_finished_gaps_ordered_oldest_first(self):
        # Within finished tier, oldest kickoff date first.
        inp = _make_input(
            "BL1",
            fixture_ids={1, 2, 3},
            covered_ids=set(),
            finished_ids={1, 2, 3},
            kickoff_by_id={
                1: date(2025, 3, 15),
                2: date(2024, 8, 10),  # oldest
                3: date(2025, 1, 5),
            },
        )
        queue = build_global_fanout_queue([inp])
        fids = [fid for _, fid in queue]
        assert fids == [2, 3, 1]  # sorted by kickoff ascending

    def test_upcoming_ordered_nearest_first(self):
        # Within upcoming tier, nearest kickoff first.
        inp = _make_input(
            "BL1",
            fixture_ids={10, 11, 12},
            covered_ids=set(),
            finished_ids=set(),
            kickoff_by_id={
                10: date(2026, 6, 1),  # nearest
                11: date(2026, 8, 15),
                12: date(2026, 7, 4),
            },
        )
        queue = build_global_fanout_queue([inp])
        fids = [fid for _, fid in queue]
        assert fids == [10, 12, 11]  # sorted by kickoff ascending

    def test_cross_competition_interleaving(self):
        # BL1 has two finished gaps; WC has one older finished gap.
        # WC's older finished gap must appear before BL1's newer ones.
        inp_bl1 = _make_input(
            "BL1",
            fixture_ids={1, 2},
            covered_ids=set(),
            finished_ids={1, 2},
            kickoff_by_id={1: date(2025, 4, 1), 2: date(2025, 4, 15)},
        )
        inp_wc = _make_input(
            "WC",
            fixture_ids={100},
            covered_ids=set(),
            finished_ids={100},
            kickoff_by_id={100: date(2024, 12, 1)},  # much older
        )
        queue = build_global_fanout_queue([inp_bl1, inp_wc])
        fids_lcs = [(lc, fid) for lc, fid in queue]
        # WC fixture 100 (Dec 2024) must come before BL1 fixtures (Apr 2025)
        wc_idx = next(i for i, (lc, fid) in enumerate(fids_lcs) if lc == "WC")
        bl1_idxs = [i for i, (lc, fid) in enumerate(fids_lcs) if lc == "BL1"]
        assert all(wc_idx < bi for bi in bl1_idxs)

    def test_already_covered_fixture_excluded(self):
        inp = _make_input(
            "BL1",
            fixture_ids={1, 2},
            covered_ids={1},  # fixture 1 is already covered
            finished_ids={1, 2},
            kickoff_by_id={1: date(2025, 1, 1), 2: date(2025, 2, 1)},
        )
        queue = build_global_fanout_queue([inp])
        fids = [fid for _, fid in queue]
        assert 1 not in fids
        assert 2 in fids

    def test_league_code_preserved_in_queue(self):
        # Each entry must carry the correct league_code so the fetcher knows where to write.
        inp_bl1 = _make_input("BL1", {10}, set(), {10}, {10: date(2025, 1, 1)})
        inp_wc = _make_input("WC", {20}, set(), {20}, {20: date(2025, 1, 1)})
        queue = build_global_fanout_queue([inp_bl1, inp_wc])
        lc_map = {fid: lc for lc, fid in queue}
        assert lc_map[10] == "BL1"
        assert lc_map[20] == "WC"
