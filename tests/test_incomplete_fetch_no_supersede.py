"""An incomplete fetch must never be written, because a written row marks its key captured.

Both halves are pinned: the refusal, and that a complete fetch is still written.
"""

from __future__ import annotations

import types
from datetime import datetime, timezone

import pytest

from ingestion.api_football import http_client, quota as errors_quota
from ingestion.api_football.loads import batch_fixtures as bf, squads as sq


def _ctx():
    return types.SimpleNamespace(
        headers={}, errors=[], client=None, add_loaded=lambda n: None
    )


def _wire(monkeypatch, fetch):
    """Run load_squad_players_batch with no network and no BigQuery, capturing the writes."""
    captured: dict = {"rows": None, "load_calls": 0, "keys": None}

    def fake_loader(client, table, rows, *, league_code, append=True, ingested_at=None):
        captured["rows"] = rows
        captured["load_calls"] += 1
        captured["keys"] = [
            f"{e['team_id']}-{e['season']}" for r in rows for e in r["response"]
        ]
        return len(rows)

    monkeypatch.setattr(sq.errors_quota, "_http_quota_exhausted", False)
    monkeypatch.setattr(sq, "captured_player_team_seasons", lambda ctx: set())
    monkeypatch.setattr(sq, "players_response_for_team", fetch)
    monkeypatch.setattr(sq, "load_json_payload_rows_to_bq", fake_loader)
    return captured


class TestIncompleteFetchDoesNotSupersede:
    def test_rate_limited_empty_response_does_not_delete_prior_rows(self, monkeypatch):
        # The provider returns 200 with a rateLimit error in the body, so the response looks successful.
        captured = _wire(monkeypatch, lambda *a, **k: ([], False))
        ctx = _ctx()
        sq.load_squad_players_batch(ctx, "UCL", [2026], {340})

        assert captured["load_calls"] == 0, "an incomplete fetch must not be written"
        assert any("SKIPPED on an incomplete fetch" in e for e in ctx.errors)

    def test_partial_pagination_does_not_supersede(self, monkeypatch):
        # Non-empty but partial: the limit hit mid-pagination, so an emptiness check cannot catch it.
        captured = _wire(
            monkeypatch, lambda *a, **k: ([{"player": {"id": i}} for i in range(40)], False)
        )
        ctx = _ctx()
        sq.load_squad_players_batch(ctx, "APD", [2026], {463})

        assert captured["load_calls"] == 0

    def test_incomplete_key_is_not_marked_captured(self, monkeypatch):
        # A written row marks the (team, season) captured, so a historical season would never be re-fetched.
        captured = _wire(monkeypatch, lambda *a, **k: ([], False))
        sq.load_squad_players_batch(_ctx(), "UCL", [2025], {340})
        assert captured["rows"] is None

    def test_one_bad_team_does_not_block_the_others(self, monkeypatch):
        # A single rejected call must not cost the whole league its refresh.
        def fetch(headers, team_id, season, errors, error_context=""):
            if team_id == 340:
                return [], False
            return [{"player": {"id": team_id}}], True

        captured = _wire(monkeypatch, fetch)
        sq.load_squad_players_batch(_ctx(), "UCL", [2026], {340, 341})

        assert captured["keys"] == ["341-2026"], "only the good key may be written"
        written = [e["team_id"] for r in captured["rows"] for e in r["response"]]
        assert written == [341]


class TestCompleteFetchIsStillWritten:
    def test_successful_fetch_is_written_as_before(self, monkeypatch):
        captured = _wire(monkeypatch, lambda *a, **k: ([{"player": {"id": 7}}], True))
        ctx = _ctx()
        sq.load_squad_players_batch(ctx, "UCL", [2026], {340})

        assert captured["load_calls"] == 1
        assert captured["keys"] == ["340-2026"]
        assert ctx.errors == []

    def test_empty_but_complete_response_is_still_written(self, monkeypatch):
        # An empty response with no error is a genuine "no players"; refusing it would re-fetch
        # every such historical team-season each night.
        captured = _wire(monkeypatch, lambda *a, **k: ([], True))
        sq.load_squad_players_batch(_ctx(), "UCL", [2026], {340})

        assert captured["load_calls"] == 1
        # The key is written with an empty players_payload so it counts as captured.
        assert captured["keys"] == ["340-2026"]
        assert captured["rows"][0]["response"][0]["players_payload"] == []


class TestResultIsComplete:
    """The completeness signal itself, pinned at the source."""

    @pytest.fixture(autouse=True)
    def _reset_quota(self):
        errors_quota.reset_http_quota_exhausted()
        yield
        errors_quota.reset_http_quota_exhausted()

    def test_body_level_error_is_incomplete(self, monkeypatch):
        # The per-minute limit is HTTP 200 with the error in the body, so http_client's 429 branch never fires.
        monkeypatch.setattr(
            http_client,
            "fetch_json",
            lambda *a, **k: {
                "response": [],
                "errors": {"rateLimit": "Too many requests."},
                "paging": {"current": 1, "total": 1},
            },
        )
        out = http_client.fetch_merged_paged("/players", {}, {"team": 1})
        assert http_client.result_is_complete(out) is False

    def test_clean_response_is_complete(self, monkeypatch):
        monkeypatch.setattr(
            http_client,
            "fetch_json",
            lambda *a, **k: {
                "response": [{"player": {"id": 1}}],
                "errors": [],
                "paging": {"current": 1, "total": 1},
            },
        )
        out = http_client.fetch_merged_paged("/players", {}, {"team": 1})
        assert http_client.result_is_complete(out) is True

    def test_empty_clean_response_is_complete(self, monkeypatch):
        monkeypatch.setattr(
            http_client,
            "fetch_json",
            lambda *a, **k: {"response": [], "errors": [], "paging": {"current": 1, "total": 1}},
        )
        out = http_client.fetch_merged_paged("/players", {}, {"team": 1})
        assert http_client.result_is_complete(out) is True

    def test_quota_cut_mid_pagination_is_incomplete(self, monkeypatch):
        # A quota-exhausted call returns an empty body with no errors, so the quota flag must be part of completeness.
        calls = {"n": 0}

        def fake_fetch_json(path, headers, params=None):
            calls["n"] += 1
            if calls["n"] >= 2:
                errors_quota._http_quota_exhausted = True
                return {"response": [], "errors": [], "paging": {"current": 2, "total": 5}}
            return {
                "response": [{"player": {"id": 1}}],
                "errors": [],
                "paging": {"current": 1, "total": 5},
            }

        monkeypatch.setattr(http_client, "fetch_json", fake_fetch_json)
        out = http_client.fetch_merged_paged("/players", {}, {"team": 1}, max_pages=5)
        assert http_client.result_is_complete(out) is False

    def test_non_paginated_error_is_incomplete(self, monkeypatch):
        # /transfers and /teams reject `page`, so they take the paginate=False branch.
        monkeypatch.setattr(
            http_client,
            "fetch_json",
            lambda *a, **k: {"response": [], "errors": {"rateLimit": "Too many requests."}},
        )
        out = http_client.fetch_merged_paged("/transfers", {}, {"team": 1}, paginate=False)
        assert http_client.result_is_complete(out) is False


class TestReturnedKeySetIsStable:
    """`fetch_merged_paged`'s dict is copied into the raw payload, so a new top-level key would land in raw tables."""

    @pytest.fixture(autouse=True)
    def _reset_quota(self):
        errors_quota.reset_http_quota_exhausted()
        yield
        errors_quota.reset_http_quota_exhausted()

    EXPECTED = {"response", "errors", "results", "paging"}

    def test_paginated_returns_only_contract_keys(self, monkeypatch):
        monkeypatch.setattr(
            http_client,
            "fetch_json",
            lambda *a, **k: {
                "response": [{"player": {"id": 1}}],
                "errors": [],
                "paging": {"current": 1, "total": 1},
            },
        )
        out = http_client.fetch_merged_paged("/players", {}, {"team": 1})
        assert set(out) == self.EXPECTED

    def test_non_paginated_returns_only_contract_keys(self, monkeypatch):
        monkeypatch.setattr(
            http_client,
            "fetch_json",
            lambda *a, **k: {"response": [], "errors": [], "paging": {"current": 1, "total": 1}},
        )
        out = http_client.fetch_merged_paged("/transfers", {}, {"team": 1}, paginate=False)
        assert set(out) == self.EXPECTED

    def test_provider_meta_keys_still_pass_through(self, monkeypatch):
        # Provider envelope fields must still flow through, because the stored raw payload is built from them.
        monkeypatch.setattr(
            http_client,
            "fetch_json",
            lambda *a, **k: {
                "get": "players",
                "parameters": {"team": "1"},
                "response": [],
                "errors": [],
                "paging": {"current": 1, "total": 1},
            },
        )
        out = http_client.fetch_merged_paged("/players", {}, {"team": 1})
        assert set(out) == self.EXPECTED | {"get", "parameters"}


def _fixture_obj(fid: int) -> dict:
    return {"fixture": {"id": fid}, "events": [], "statistics": [{"team": {"id": 1}}]}


class _RecordingClient:
    """Records every query. `_fetch_and_persist_batch` must issue none."""

    def __init__(self):
        self.queries: list[str] = []

    def query(self, sql, job_config=None):
        self.queries.append(sql)
        return types.SimpleNamespace(result=lambda: None)


def _wire_batch(monkeypatch, data: dict) -> dict:
    """Run the real _fetch_and_persist_batch with no network and no BigQuery.

    Any DML must travel through `ctx.client.query`, so the recording client catches a delete under any name.
    """
    captured: dict = {"inserted": None}

    monkeypatch.setattr(bf.errors_quota, "_http_quota_exhausted", False)
    monkeypatch.setattr(bf, "fetch_json", lambda *a, **k: data)
    monkeypatch.setattr(bf, "ensure_unified_raw_table", lambda *a, **k: None)
    monkeypatch.setattr(
        bf,
        "_insert_fixture_rows",
        lambda client, table_name, response, ts, league_code: captured.__setitem__(
            "inserted", [r["fixture"]["id"] for r in response]
        ),
    )
    return captured


class TestFixtureDetailsRetryKeepsBothVersions:
    """A fixture-details row bundles several sections, so a retry can be poorer in one; raw keeps both versions."""

    def test_a_retried_fixture_is_appended_and_nothing_is_deleted(self, monkeypatch):
        # 111 is retried and answered cleanly, so its new version is appended beside the old one.
        # 222 is retried and not returned, so it is simply not written.
        data = {"response": [_fixture_obj(111)], "errors": []}
        captured = _wire_batch(monkeypatch, data)
        client = _RecordingClient()
        ctx = _ctx()
        ctx.client = client

        bf._fetch_and_persist_batch(ctx, "CIT", [111, 222])

        assert captured["inserted"] == [111], (
            f"the returned fixture was not appended. inserted={captured['inserted']}"
        )
        assert client.queries == [], (
            f"a DELETE reached BigQuery: {client.queries}. Raw keeps both versions "
            "(CPO 2026-08-17) — the older payload is the only copy of anything the retry drops."
        )

    def test_incomplete_fetch_is_discarded_whole(self, monkeypatch):
        # The batch is partial, not empty, because an empty body returns early at `if not response`
        # and would pass without the guard; the whole batch is discarded and retried next run.
        data = {"response": [_fixture_obj(111)], "errors": {"rateLimit": "Too many requests"}}
        captured = _wire_batch(monkeypatch, data)
        client = _RecordingClient()
        ctx = _ctx()
        ctx.client = client

        bf._fetch_and_persist_batch(ctx, "CIT", [111, 222])

        assert captured["inserted"] is None, (
            "a known-partial payload was written. Append-only makes this recoverable rather "
            "than fatal, which is not a reason to put a worse row in front of base (#896)."
        )
        assert client.queries == []
        assert any("INCOMPLETE" in e for e in ctx.errors), ctx.errors

    def test_the_fixture_write_is_an_append(self, monkeypatch):
        # A write disposition of WRITE_TRUNCATE would destroy the table without issuing a DELETE.
        # The real `_insert_fixture_rows` runs; only the BigQuery load job is doubled.
        captured: dict = {}

        class _LoadClient:
            def load_table_from_file(self, fileobj, table_id, job_config=None):
                captured["disposition"] = job_config.write_disposition
                return types.SimpleNamespace(result=lambda: None)

        bf._insert_fixture_rows(
            _LoadClient(),
            "RAW_APIF_FIXTURE_DETAILS",
            [_fixture_obj(111)],
            datetime(2026, 8, 17, tzinfo=timezone.utc),
            "CIT",
        )

        assert captured["disposition"] == "WRITE_APPEND", (
            f"fixture details were written with {captured['disposition']!r}. Anything but "
            "WRITE_APPEND erases the table's history for every competition at once."
        )
