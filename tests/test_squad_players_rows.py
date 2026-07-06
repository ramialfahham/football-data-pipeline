"""Tests for RAW_APIF_PLAYERS one-row-per-(team, season) writes (the >100 MB load fix).

The players snapshot is written as one small row per (team, season) — not one giant
per-league row — so no single row can approach BigQuery's 100 MB per-row JSON limit,
for any league (mirrors RAW_APIF_FIXTURE_DETAILS, one row per fixture). These tests
cover the loader grain (one row per team×season, none lost) against a committed real
/players slice, and the atomic multi-row writer.
"""

from __future__ import annotations

import json
import types
from pathlib import Path

from ingestion.api_football.loads import squads as sq
from ingestion.api_football import bigquery as bq
from ingestion.api_football.settings import DATASET_ID, GCP_PROJECT_ID

_FIXTURE = Path(__file__).parent / "fixtures" / "apif" / "players_cwc_sample.json"


def _load_fixture() -> dict:
    return json.loads(_FIXTURE.read_text(encoding="utf-8"))


# --- load_squad_players_batch: one small row per (team, season), no network ---


def test_writes_one_row_per_team_season_from_real_payload(monkeypatch):
    fixture = _load_fixture()
    by_key = {
        (e["team_id"], e["season"]): e["players_payload"] for e in fixture["response"]
    }

    def fake_fetch(headers, team_id, season, errors, error_context=""):
        return by_key.get((team_id, season), [])

    monkeypatch.setattr(sq, "players_response_for_team", fake_fetch)
    monkeypatch.setattr(sq.errors_quota, "_http_quota_exhausted", False)
    # The fetch-side skip reads BQ for captured (team, season); the fake ctx has no client, so
    # stub the reader to "nothing captured" — the single season here is the reference season and
    # is fetched regardless.
    monkeypatch.setattr(sq, "captured_player_team_seasons", lambda ctx: set())

    captured: dict = {}

    def fake_loader(client, table, rows, *, league_code, append=True, ingested_at=None):
        captured["rows"] = rows
        captured["league_code"] = league_code
        captured["ingested_at"] = ingested_at
        return len(rows)

    def fake_delete(client, table, league_code, keys, before):
        captured["delete_keys"] = keys
        captured["delete_before"] = before

    monkeypatch.setattr(sq, "load_json_payload_rows_to_bq", fake_loader)
    monkeypatch.setattr(sq, "_delete_superseded_player_rows", fake_delete)

    ctx = types.SimpleNamespace(
        headers={}, errors=[], client=None, add_loaded=lambda n: None
    )
    sq.load_squad_players_batch(ctx, "CWC", [2016], {40, 49})

    rows = captured["rows"]
    assert captured["league_code"] == "CWC"
    assert len(rows) == 2  # one row per (team, season) — not one giant row
    for r in rows:
        assert r["league_code"] == "CWC"
        assert len(r["response"]) == 1  # exactly one team×season entry per row (small)
    # Every (team, season) present exactly once; both real players preserved.
    team_seasons = sorted(
        (e["team_id"], e["season"]) for r in rows for e in r["response"]
    )
    assert team_seasons == [(40, 2016), (49, 2016)]
    ids = sorted(
        p["player"]["id"]
        for r in rows
        for e in r["response"]
        for p in e["players_payload"]
    )
    assert ids == [54, 281]
    # Merge-on-write: the superseded prior rows for exactly the written keys are deleted,
    # using the same ingested_at the rows were written with.
    assert sorted(captured["delete_keys"]) == ["40-2016", "49-2016"]
    assert captured["delete_before"].isoformat() == captured["ingested_at"]
    assert ctx.errors == []


def test_no_rows_means_no_write(monkeypatch):
    monkeypatch.setattr(sq.errors_quota, "_http_quota_exhausted", False)
    monkeypatch.setattr(sq, "captured_player_team_seasons", lambda ctx: set())
    monkeypatch.setattr(
        sq, "players_response_for_team", lambda *a, **k: (_ for _ in ()).throw(AssertionError("should not fetch"))
    )
    called = {"n": 0}
    monkeypatch.setattr(
        sq, "load_json_payload_rows_to_bq", lambda *a, **k: called.__setitem__("n", called["n"] + 1)
    )
    ctx = types.SimpleNamespace(headers={}, errors=[], client=None, add_loaded=lambda n: None)
    sq.load_squad_players_batch(ctx, "CWC", [2016], set())  # no teams -> nothing fetched
    assert called["n"] == 0  # no load job when there is nothing to write


def test_quota_cut_logs_partial_warning(monkeypatch):
    # A quota cut mid-fetch must NOT report a silent success — a PARTIAL warning is logged.
    monkeypatch.setattr(sq.errors_quota, "_http_quota_exhausted", False)
    monkeypatch.setattr(sq, "captured_player_team_seasons", lambda ctx: set())

    def fake_fetch(headers, team_id, season, errors, error_context=""):
        monkeypatch.setattr(sq.errors_quota, "_http_quota_exhausted", True)  # exhaust after first
        return [{"player": {"id": 1}}]

    monkeypatch.setattr(sq, "players_response_for_team", fake_fetch)
    monkeypatch.setattr(sq, "load_json_payload_rows_to_bq", lambda *a, **k: 1)
    monkeypatch.setattr(sq, "_delete_superseded_player_rows", lambda *a, **k: None)
    ctx = types.SimpleNamespace(headers={}, errors=[], client=None, add_loaded=lambda n: None)
    sq.load_squad_players_batch(ctx, "CWC", [2016], {40, 49})
    assert any("PARTIAL" in e for e in ctx.errors)


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
    monkeypatch.setattr(bq, "ensure_unified_raw_table", lambda *a, **k: None)
    client = _CapturingClient()
    payloads = [
        {"league_code": "CWC", "response": [{"team_id": 40, "season": 2016}]},
        {"league_code": "CWC", "response": [{"team_id": 49, "season": 2016}]},
    ]
    written = bq.load_json_payload_rows_to_bq(
        client, "RAW_APIF_PLAYERS", payloads, league_code="CWC", append=True
    )
    assert written == 2
    assert len(client.calls) == 1  # ONE atomic load job for the whole snapshot
    call = client.calls[0]
    assert call["write_disposition"] == "WRITE_APPEND"
    rows = [json.loads(line) for line in call["data"].splitlines() if line.strip()]
    assert len(rows) == 2
    assert len({r["ingested_at"] for r in rows}) == 1  # all rows share one ingested_at
    assert all(r["league_code"] == "CWC" for r in rows)
    assert [r["payload"]["response"][0]["team_id"] for r in rows] == [40, 49]


def test_multi_row_loader_empty_writes_nothing():
    client = _CapturingClient()
    written = bq.load_json_payload_rows_to_bq(
        client, "RAW_APIF_PLAYERS", [], league_code="CWC", append=True
    )
    assert written == 0
    assert client.calls == []


# --- plan_player_team_season_fetch: fetch-side skip policy (pure, no I/O) ---
# The reference (live) season is always re-fetched (per-season stats accumulate); earlier
# seasons are immutable and fetched only when their (team, season) is not already held.


def test_plan_reference_season_always_fetched_even_if_captured():
    plan = sq.plan_player_team_season_fetch(
        seasons_list=[2024, 2025],
        team_ids={10, 11},
        reference_season=2025,
        already_captured={(10, 2025), (11, 2025), (10, 2024), (11, 2024)},
    )
    # 2025 (reference) re-fetched despite being held; 2024 fully held -> skipped.
    assert plan == [(2025, 10), (2025, 11)]


def test_plan_historical_gap_self_heals():
    plan = sq.plan_player_team_season_fetch(
        seasons_list=[2024, 2025],
        team_ids={10, 11},
        reference_season=2025,
        already_captured={(10, 2024)},
    )
    # 2024: only team 11 missing -> fetched; 2025 (reference): both.
    assert plan == [(2024, 11), (2025, 10), (2025, 11)]


def test_plan_first_run_fetches_full_product():
    plan = sq.plan_player_team_season_fetch(
        seasons_list=[2024, 2025],
        team_ids={10, 11},
        reference_season=2025,
        already_captured=set(),
    )
    # Nothing held (first run / backfill) -> the whole season×team product.
    assert plan == [(2024, 10), (2024, 11), (2025, 10), (2025, 11)]


def test_plan_empty_inputs():
    assert sq.plan_player_team_season_fetch([], {10}, 2025, set()) == []
    assert sq.plan_player_team_season_fetch([2025], set(), 2025, set()) == []


# --- captured_player_team_seasons: BigQuery read of already-stored (team, season) pairs ---
# Fake client so the Python row-handling runs with NO network; the JSON-path SQL itself is
# validated against real RAW_APIF_PLAYERS separately (mirrors test_player_squads_catchup).


class _FakeResult:
    def __init__(self, rows):
        self._rows = rows

    def result(self):
        return self._rows


class _FakeClient:
    def __init__(self, rows=None, raise_exc=None):
        self._rows = rows or []
        self._raise = raise_exc
        self.last_sql = None

    def query(self, sql):
        self.last_sql = sql
        if self._raise is not None:
            raise self._raise
        return _FakeResult(self._rows)


def _skip_ctx(rows=None, raise_exc=None):
    return types.SimpleNamespace(client=_FakeClient(rows=rows, raise_exc=raise_exc), errors=[])


def _row(team_id, season):
    return types.SimpleNamespace(team_id=team_id, season=season)


def test_captured_player_team_seasons_returns_pairs():
    ctx = _skip_ctx(rows=[_row(10, 2025), _row(11, 2025), _row(10, 2024)])
    assert sq.captured_player_team_seasons(ctx) == {(10, 2025), (11, 2025), (10, 2024)}
    assert ctx.errors == []


def test_captured_player_team_seasons_skips_null_rows():
    ctx = _skip_ctx(rows=[_row(10, 2025), _row(None, 2025), _row(11, None)])
    assert sq.captured_player_team_seasons(ctx) == {(10, 2025)}


def test_captured_player_team_seasons_failopen_on_query_error():
    # A read failure must not abort the run; return empty (re-capture is the safe direction).
    ctx = _skip_ctx(raise_exc=RuntimeError("boom"))
    assert sq.captured_player_team_seasons(ctx) == set()
    assert any("captured-seasons read failed" in e for e in ctx.errors)


def test_captured_player_team_seasons_query_is_fully_qualified():
    # Regression guard: a bare table name fails at runtime; the read must reference
    # project.dataset.RAW_APIF_PLAYERS (matches _fq in loads/player_universe.py).
    ctx = _skip_ctx(rows=[])
    sq.captured_player_team_seasons(ctx)
    assert f"{GCP_PROJECT_ID}.{DATASET_ID}." in ctx.client.last_sql
    assert "RAW_APIF_PLAYERS" in ctx.client.last_sql
