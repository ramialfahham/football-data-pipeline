"""Tests for merge.py — the remaining merge helpers.

The five reference-table merge functions (fixtures, standings, teams, transfers,
players) were removed in issue #220 when those tables switched to append-only
writes. Each pipeline run now writes a complete fresh snapshot, so cross-run
merging is no longer needed for those tables.

One merge function remains and is tested here:

- merge_fanout_batched: still used by the per-fixture fanout tables (lineups,
  events, stats, fixture players, predictions), which remain merge-on-write
  until issue #221 introduces the fixture coverage tracking table.
"""

import pytest
from ingestion.api_football.merge import merge_fanout_batched


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
