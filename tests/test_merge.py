"""Tests for merge.py — the merge-on-write payload functions.

Every raw BQ table holds a single merged JSON payload. These functions are called
on every ingestion run; a bug here silently corrupts or loses historical data.
"""

import pytest
from ingestion.api_football.merge import (
    merge_fanout_batched,
    merge_fixtures_envelope,
    merge_players_squad,
    merge_rounds_season_blocks,
    merge_standings_envelope,
    merge_teams_envelope,
    merge_transfers_envelope,
)


# ---------------------------------------------------------------------------
# merge_fixtures_envelope
# ---------------------------------------------------------------------------

def _fixture(fid: int, status: str = "FT") -> dict:
    return {"fixture": {"id": fid, "status": {"short": status}}, "teams": {}}


class TestMergeFixturesEnvelope:
    def test_first_run_no_existing(self):
        incoming = {"response": [_fixture(1), _fixture(2)], "errors": []}
        result = merge_fixtures_envelope(None, incoming)
        assert {r["fixture"]["id"] for r in result["response"]} == {1, 2}

    def test_incoming_overwrites_existing_on_same_id(self):
        existing = {"response": [_fixture(1, "NS"), _fixture(2, "FT")]}
        incoming = {"response": [_fixture(1, "FT")], "errors": []}
        result = merge_fixtures_envelope(existing, incoming)
        by_id = {r["fixture"]["id"]: r for r in result["response"]}
        assert by_id[1]["fixture"]["status"]["short"] == "FT"
        assert by_id[2]["fixture"]["status"]["short"] == "FT"

    def test_existing_fixture_not_in_incoming_is_preserved(self):
        existing = {"response": [_fixture(1), _fixture(2)]}
        incoming = {"response": [_fixture(3)], "errors": []}
        result = merge_fixtures_envelope(existing, incoming)
        ids = {r["fixture"]["id"] for r in result["response"]}
        assert ids == {1, 2, 3}

    def test_results_count_matches_response_length(self):
        existing = {"response": [_fixture(1), _fixture(2)]}
        incoming = {"response": [_fixture(3)], "errors": []}
        result = merge_fixtures_envelope(existing, incoming)
        assert result["results"] == len(result["response"])

    def test_response_sorted_by_fixture_id(self):
        existing = {"response": [_fixture(10), _fixture(5)]}
        incoming = {"response": [_fixture(7)], "errors": []}
        result = merge_fixtures_envelope(existing, incoming)
        ids = [r["fixture"]["id"] for r in result["response"]]
        assert ids == sorted(ids)

    def test_empty_existing_empty_incoming(self):
        result = merge_fixtures_envelope(None, {"response": [], "errors": []})
        assert result["response"] == []
        assert result["results"] == 0


# ---------------------------------------------------------------------------
# merge_fanout_batched
# ---------------------------------------------------------------------------

def _fanout_row(fid: int, data: str = "x") -> dict:
    return {"fixture_id": fid, "lineups": data}


class TestMergeFanoutBatched:
    def test_first_run(self):
        incoming = {"league_code": "BL1", "response": [_fanout_row(1), _fanout_row(2)]}
        result = merge_fanout_batched(None, incoming, league_code="BL1", valid_fixture_ids={1, 2})
        assert len(result["response"]) == 2

    def test_incoming_overwrites_existing(self):
        existing = {"league_code": "BL1", "response": [_fanout_row(1, "old")]}
        incoming = {"league_code": "BL1", "response": [_fanout_row(1, "new")]}
        result = merge_fanout_batched(existing, incoming, league_code="BL1", valid_fixture_ids={1})
        assert result["response"][0]["lineups"] == "new"

    def test_stale_fixture_id_pruned(self):
        existing = {"league_code": "BL1", "response": [_fanout_row(1), _fanout_row(99)]}
        incoming = {"league_code": "BL1", "response": []}
        # fixture 99 is no longer valid (cancelled match)
        result = merge_fanout_batched(existing, incoming, league_code="BL1", valid_fixture_ids={1})
        ids = {r["fixture_id"] for r in result["response"]}
        assert 99 not in ids
        assert 1 in ids

    def test_valid_fixture_ids_none_keeps_all(self):
        existing = {"league_code": "BL1", "response": [_fanout_row(1), _fanout_row(2)]}
        incoming = {"league_code": "BL1", "response": []}
        result = merge_fanout_batched(existing, incoming, league_code="BL1", valid_fixture_ids=None)
        assert len(result["response"]) == 2

    def test_sorted_by_fixture_id(self):
        existing = {"league_code": "BL1", "response": [_fanout_row(10), _fanout_row(3)]}
        incoming = {"league_code": "BL1", "response": [_fanout_row(7)]}
        result = merge_fanout_batched(existing, incoming, league_code="BL1", valid_fixture_ids={3, 7, 10})
        ids = [r["fixture_id"] for r in result["response"]]
        assert ids == sorted(ids)

    def test_empty_statistics_does_not_overwrite_nonempty(self):
        existing = {
            "league_code": "WCQAF",
            "response": [
                {
                    "fixture_id": 256075,
                    "statistics": [{"team": {"id": 1}, "statistics": [{"type": "Shots on Goal"}]}],
                }
            ],
        }
        incoming = {
            "league_code": "WCQAF",
            "response": [{"fixture_id": 256075, "statistics": []}],
        }
        result = merge_fanout_batched(
            existing, incoming, league_code="WCQAF", valid_fixture_ids={256075}
        )
        row = result["response"][0]
        assert row["fixture_id"] == 256075
        assert len(row["statistics"]) == 1

    def test_nonempty_statistics_overwrites_empty(self):
        existing = {
            "league_code": "WCQAF",
            "response": [{"fixture_id": 256075, "statistics": []}],
        }
        incoming = {
            "league_code": "WCQAF",
            "response": [
                {
                    "fixture_id": 256075,
                    "statistics": [{"team": {"id": 1}, "statistics": [{"type": "Shots on Goal"}]}],
                }
            ],
        }
        result = merge_fanout_batched(
            existing, incoming, league_code="WCQAF", valid_fixture_ids={256075}
        )
        assert len(result["response"][0]["statistics"]) == 1


# ---------------------------------------------------------------------------
# merge_rounds_season_blocks
# ---------------------------------------------------------------------------

class TestMergeRoundsSeasonBlocks:
    def _rounds(self, names):
        return {"response": names, "errors": []}

    def test_first_season(self):
        result = merge_rounds_season_blocks(None, 2024, self._rounds(["Round 1", "Round 2"]))
        assert len(result["response"]) == 1
        assert result["response"][0]["season"] == 2024
        assert result["response"][0]["rounds"] == ["Round 1", "Round 2"]

    def test_second_season_appended(self):
        first = merge_rounds_season_blocks(None, 2023, self._rounds(["Round 1"]))
        second = merge_rounds_season_blocks(first, 2024, self._rounds(["Round 1", "Round 2"]))
        seasons = [b["season"] for b in second["response"]]
        assert seasons == [2023, 2024]

    def test_same_season_overwrites(self):
        first = merge_rounds_season_blocks(None, 2024, self._rounds(["Round 1"]))
        updated = merge_rounds_season_blocks(first, 2024, self._rounds(["Round 1", "Round 2", "Round 3"]))
        blocks = {b["season"]: b for b in updated["response"]}
        assert len(blocks[2024]["rounds"]) == 3

    def test_legacy_flat_payload_discarded(self):
        # Old format: response is a flat list of strings, not season blocks
        legacy = {"response": ["Regular Season - 1", "Regular Season - 2"], "errors": []}
        result = merge_rounds_season_blocks(legacy, 2024, self._rounds(["Round 1"]))
        # Legacy data should not corrupt the new tagged format
        for block in result["response"]:
            assert isinstance(block, dict)
            assert "season" in block

    def test_sorted_by_season(self):
        r1 = merge_rounds_season_blocks(None, 2022, self._rounds(["R1"]))
        r2 = merge_rounds_season_blocks(r1, 2024, self._rounds(["R1"]))
        r3 = merge_rounds_season_blocks(r2, 2023, self._rounds(["R1"]))
        seasons = [b["season"] for b in r3["response"]]
        assert seasons == sorted(seasons)


# ---------------------------------------------------------------------------
# merge_players_squad
# ---------------------------------------------------------------------------

class TestMergePlayersSquad:
    def _row(self, team_id, season, data="x"):
        return {"team_id": team_id, "season": season, "players_payload": data}

    def test_first_run(self):
        incoming = {"league_code": "BL1", "response": [self._row(10, 2024)]}
        result = merge_players_squad(None, incoming, league_code="BL1", valid_team_season={(10, 2024)})
        assert len(result["response"]) == 1

    def test_incoming_overwrites_existing(self):
        existing = {"league_code": "BL1", "response": [self._row(10, 2024, "old")]}
        incoming = {"league_code": "BL1", "response": [self._row(10, 2024, "new")]}
        result = merge_players_squad(existing, incoming, league_code="BL1", valid_team_season={(10, 2024)})
        assert result["response"][0]["players_payload"] == "new"

    def test_stale_team_season_pruned(self):
        existing = {"league_code": "BL1", "response": [self._row(10, 2020), self._row(10, 2024)]}
        incoming = {"league_code": "BL1", "response": []}
        result = merge_players_squad(existing, incoming, league_code="BL1", valid_team_season={(10, 2024)})
        seasons = {r["season"] for r in result["response"]}
        assert 2020 not in seasons
        assert 2024 in seasons


# ---------------------------------------------------------------------------
# merge_standings_envelope
# ---------------------------------------------------------------------------

class TestMergeStandingsEnvelope:
    def _standing(self, season):
        return {"league": {"season": season, "name": "Bundesliga"}, "standings": [[]]}

    def test_first_run(self):
        incoming = {"response": [self._standing(2024)], "errors": []}
        result = merge_standings_envelope(None, incoming)
        assert len(result["response"]) == 1

    def test_multi_season_merge(self):
        existing = {"response": [self._standing(2023)]}
        incoming = {"response": [self._standing(2024)], "errors": []}
        result = merge_standings_envelope(existing, incoming)
        seasons = {r["league"]["season"] for r in result["response"]}
        assert seasons == {2023, 2024}

    def test_same_season_overwrites(self):
        existing = {"response": [self._standing(2024)]}
        updated = {"league": {"season": 2024, "name": "Bundesliga"}, "standings": [["new"]]}
        incoming = {"response": [updated], "errors": []}
        result = merge_standings_envelope(existing, incoming)
        assert len(result["response"]) == 1
        assert result["response"][0]["standings"] == [["new"]]


# ---------------------------------------------------------------------------
# merge_teams_envelope
# ---------------------------------------------------------------------------

class TestMergeTeamsEnvelope:
    def _team(self, team_id, season):
        return {"team": {"id": team_id}, "league": {"season": season}}

    def test_multi_season_teams_preserved(self):
        existing = {"response": [self._team(1, 2023), self._team(2, 2023)]}
        incoming = {"response": [self._team(1, 2024)], "errors": []}
        result = merge_teams_envelope(existing, incoming)
        keys = {(r["team"]["id"], r["league"]["season"]) for r in result["response"]}
        assert (1, 2023) in keys
        assert (2, 2023) in keys
        assert (1, 2024) in keys


# ---------------------------------------------------------------------------
# merge_transfers_envelope
# ---------------------------------------------------------------------------

class TestMergeTransfersEnvelope:
    def _transfer(self, player_id):
        return {"player": {"id": player_id, "name": f"Player {player_id}"}, "transfers": []}

    def test_new_player_added(self):
        existing = {"response": [self._transfer(10)], "errors": []}
        incoming = {"response": [self._transfer(20)], "errors": []}
        result = merge_transfers_envelope(existing, incoming)
        ids = {r["player"]["id"] for r in result["response"]}
        assert ids == {10, 20}

    def test_existing_player_overwritten(self):
        existing = {"response": [{"player": {"id": 10}, "transfers": ["old"]}], "errors": []}
        incoming = {"response": [{"player": {"id": 10}, "transfers": ["new"]}], "errors": []}
        result = merge_transfers_envelope(existing, incoming)
        assert result["response"][0]["transfers"] == ["new"]
