"""Tests for RAW_APIF_PLAYERS snapshot chunking (the >100 MB single-row load fix).

A large-roster deep league's /players snapshot exceeds BigQuery's 100 MB per-row JSON
limit, so loads/squads.py splits it into byte-bounded chunk rows written in ONE atomic
load job sharing a single ingested_at. These tests cover the pure chunker (no entry is
lost or reordered; the row budget is respected) and the atomic multi-row loader (one
load job, one shared ingested_at, league_code stamped).
"""

from __future__ import annotations

import json
import types
from pathlib import Path

from ingestion.api_football.loads.squads import (
    chunk_players_response,
    _entry_bytes,
)

_FIXTURE = Path(__file__).parent / "fixtures" / "apif" / "players_cwc_sample.json"


def _entry(team_id: int, season: int, blob_chars: int = 0) -> dict:
    # players_payload padded to a controllable size so chunk boundaries are deterministic.
    return {
        "team_id": team_id,
        "season": season,
        "players_payload": [{"x": "a" * blob_chars}] if blob_chars else [],
    }


def _all_team_seasons(chunks: list[dict]) -> list[tuple[int, int]]:
    out: list[tuple[int, int]] = []
    for payload in chunks:
        for e in payload["response"]:
            out.append((e["team_id"], e["season"]))
    return out


# --- chunk_players_response: pure, no I/O ---


def test_empty_response_yields_one_empty_snapshot_row():
    chunks = chunk_players_response("LIBER", [], max_row_bytes=40_000_000)
    assert chunks == [{"league_code": "LIBER", "response": []}]


def test_small_response_stays_one_row():
    entries = [_entry(10, 2025), _entry(11, 2025), _entry(12, 2025)]
    chunks = chunk_players_response("PL", entries, max_row_bytes=40_000_000)
    assert len(chunks) == 1
    assert all(c["league_code"] == "PL" for c in chunks)
    assert _all_team_seasons(chunks) == [(10, 2025), (11, 2025), (12, 2025)]


def test_splits_when_over_budget_and_preserves_all_entries_in_order():
    # Each padded entry is ~1000 bytes; a 2500-byte budget => 2 entries per chunk.
    entries = [_entry(i, 2025, blob_chars=1000) for i in range(1, 6)]  # 5 entries
    chunks = chunk_players_response("UEL", entries, max_row_bytes=2500)
    assert len(chunks) > 1
    # No entry dropped, original order preserved across chunks.
    assert _all_team_seasons(chunks) == [(i, 2025) for i in range(1, 6)]
    # Every chunk's ascii-escaped entry bytes are within budget (a non-oversize chunk).
    for c in chunks:
        assert sum(_entry_bytes(e) for e in c["response"]) <= 2500


def test_oversize_single_entry_gets_its_own_chunk_not_dropped():
    big = _entry(99, 2025, blob_chars=5000)  # alone exceeds the 2500 budget
    entries = [_entry(1, 2025, blob_chars=1000), big, _entry(2, 2025, blob_chars=1000)]
    chunks = chunk_players_response("UCL", entries, max_row_bytes=2500)
    # The oversize entry survives, in order, isolated in its own chunk.
    assert (99, 2025) in _all_team_seasons(chunks)
    assert _all_team_seasons(chunks) == [(1, 2025), (99, 2025), (2, 2025)]
    big_chunk = [c for c in chunks if any(e["team_id"] == 99 for e in c["response"])]
    assert len(big_chunk) == 1 and len(big_chunk[0]["response"]) == 1


# --- load_json_payload_rows_to_bq: one atomic job, one shared ingested_at ---


class _FakeJob:
    def result(self):
        return None


class _CapturingClient:
    def __init__(self):
        self.calls: list[dict] = []

    def load_table_from_file(self, fileobj, table_id, job_config=None):
        self.calls.append(
            {
                "data": fileobj.read().decode("utf-8"),
                "table_id": table_id,
                "write_disposition": job_config.write_disposition,
            }
        )
        return _FakeJob()


def test_multi_row_loader_writes_one_job_with_shared_ingested_at(monkeypatch):
    from ingestion.api_football import bigquery as bq

    monkeypatch.setattr(bq, "ensure_unified_raw_table", lambda *a, **k: None)
    client = _CapturingClient()
    payloads = [
        {"league_code": "LIBER", "response": [{"team_id": 1, "season": 2025}]},
        {"league_code": "LIBER", "response": [{"team_id": 2, "season": 2025}]},
        {"league_code": "LIBER", "response": [{"team_id": 3, "season": 2025}]},
    ]
    written = bq.load_json_payload_rows_to_bq(
        client, "RAW_APIF_PLAYERS", payloads, league_code="LIBER", append=True
    )
    assert written == 3
    # Exactly ONE load job (atomic — all rows land together or not at all).
    assert len(client.calls) == 1
    call = client.calls[0]
    assert call["write_disposition"] == "WRITE_APPEND"
    rows = [json.loads(line) for line in call["data"].splitlines() if line.strip()]
    assert len(rows) == 3
    # All rows share one ingested_at and carry the league_code + their chunk payload.
    assert len({r["ingested_at"] for r in rows}) == 1
    assert all(r["league_code"] == "LIBER" for r in rows)
    assert [r["payload"]["response"][0]["team_id"] for r in rows] == [1, 2, 3]


def test_multi_row_loader_empty_payloads_writes_nothing():
    client = _CapturingClient()
    written = __import__(
        "ingestion.api_football.bigquery", fromlist=["load_json_payload_rows_to_bq"]
    ).load_json_payload_rows_to_bq(
        client, "RAW_APIF_PLAYERS", [], league_code="LIBER", append=True
    )
    assert written == 0
    assert client.calls == []


# --- load_squad_players_batch: end-to-end chunking with a tiny budget (no network) ---


def test_load_squad_players_batch_chunks_under_small_budget(monkeypatch):
    from ingestion.api_football.loads import squads as sq

    from ingestion.api_football import quota as q

    monkeypatch.setattr(q, "_http_quota_exhausted", False)
    monkeypatch.setenv("API_FOOTBALL_PLAYERS_MAX_ROW_BYTES", "1000000")  # floored to 1 MB

    # Each team returns a ~400 KB roster blob → several teams force multiple chunks.
    def fake_players(headers, team_id, season, errors, error_context=""):
        return [{"player": {"id": team_id * 1000 + season}, "blob": "a" * 400_000}]

    monkeypatch.setattr(sq, "players_response_for_team", fake_players)

    captured: list[dict] = []

    def fake_loader(client, table, payloads, *, league_code, append=True):
        captured.append({"payloads": payloads, "league_code": league_code})
        return len(payloads)

    monkeypatch.setattr(sq, "load_json_payload_rows_to_bq", fake_loader)

    ctx = types.SimpleNamespace(
        headers={}, errors=[], client=None, add_loaded=lambda n: None
    )
    sq.load_squad_players_batch(ctx, "LIBER", [2024, 2025], {10, 11, 12})

    assert len(captured) == 1  # one logical players load for the league
    payloads = captured[0]["payloads"]
    assert len(payloads) > 1  # split into multiple chunk rows under the 1 MB budget
    # All 6 team×season entries present exactly once, none lost to chunking.
    seen = [
        (e["team_id"], e["season"])
        for p in payloads
        for e in p["response"]
    ]
    expected = [(t, s) for s in (2024, 2025) for t in (10, 11, 12)]
    assert len(seen) == len(expected)  # each team×season exactly once, none lost
    assert sorted(seen) == sorted(expected)


# --- chunk_players_response against a COMMITTED real /players payload slice ---
# A real CWC snapshot trimmed to 2 team×season entries, at the true api-football shape
# ({team_id, season, players_payload:[{player, statistics:[...]}]}, accented names and all).
# Guards the chunker AND the chunked row shape that stg_apif__players unnests against the
# real wire format, not just synthetic dicts (data-engineer reviewer rule).


def _load_fixture() -> dict:
    return json.loads(_FIXTURE.read_text(encoding="utf-8"))


def test_real_payload_has_expected_shape():
    snap = _load_fixture()
    assert snap["league_code"] == "CWC"
    entries = snap["response"]
    assert len(entries) == 2
    for e in entries:
        assert set(e) >= {"team_id", "season", "players_payload"}
        assert isinstance(e["players_payload"], list) and e["players_payload"]
        player = e["players_payload"][0]
        assert "player" in player and isinstance(player["statistics"], list)


def test_chunk_real_payload_splits_and_preserves_every_player():
    entries = _load_fixture()["response"]
    # A budget just under a single real entry forces one chunk per entry — exercises real sizes.
    chunks = chunk_players_response("CWC", entries, max_row_bytes=_entry_bytes(entries[0]))
    assert len(chunks) == len(entries)
    assert all(c["league_code"] == "CWC" for c in chunks)
    # Every team×season preserved in order, none dropped.
    assert _all_team_seasons(chunks) == [(40, 2016), (49, 2016)]
    # The chunked rows expose exactly the player ids stg_apif__players unnests
    # ($.response[].players_payload[].player.id) — union across chunks, no loss or duplication.
    ids = sorted(
        p["player"]["id"]
        for c in chunks
        for e in c["response"]
        for p in e["players_payload"]
    )
    assert ids == [54, 281]
