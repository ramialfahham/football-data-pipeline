"""An incomplete /players fetch must never supersede stored data (#896).

The defect: `_delete_superseded_player_rows` deleted the prior row for a (team, season) keyed on
what the NEW row claimed, with no check that the fetch had succeeded. A per-minute rate limit
arrives as HTTP 200 with the error in the body, so a rejected call looked like an empty-but-valid
squad and destroyed the good rows it failed to replace. Measured on the 2026-08-02 nightly: UCL 340
went 25 players to 0, UEL 573 24 to 0, UECL 20034 23 to 0, and APD 463 46 to 40 when the limit hit
mid-pagination.

No existing test could catch this class and none could be written against the old signals: the
TABLE GREW while the data was destroyed, so row-count, freshness and not-null checks all passed.

These tests pin both halves of the rule, because pinning only the refusal would let a fix that
never supersedes anything pass.
"""

from __future__ import annotations

import types

import pytest

from ingestion.api_football import http_client, quota as errors_quota
from ingestion.api_football.loads import squads as sq


def _ctx():
    return types.SimpleNamespace(
        headers={}, errors=[], client=None, add_loaded=lambda n: None
    )


def _wire(monkeypatch, fetch):
    """Run load_squad_players_batch with no network and no BigQuery, capturing the writes."""
    captured: dict = {"rows": None, "delete_keys": None, "load_calls": 0}

    def fake_loader(client, table, rows, *, league_code, append=True, ingested_at=None):
        captured["rows"] = rows
        captured["load_calls"] += 1
        return len(rows)

    def fake_delete(client, table, league_code, keys, before):
        captured["delete_keys"] = keys

    monkeypatch.setattr(sq.errors_quota, "_http_quota_exhausted", False)
    monkeypatch.setattr(sq, "captured_player_team_seasons", lambda ctx: set())
    monkeypatch.setattr(sq, "players_response_for_team", fetch)
    monkeypatch.setattr(sq, "load_json_payload_rows_to_bq", fake_loader)
    monkeypatch.setattr(sq, "_delete_superseded_player_rows", fake_delete)
    return captured


class TestIncompleteFetchDoesNotSupersede:
    def test_rate_limited_empty_response_does_not_delete_prior_rows(self, monkeypatch):
        # THE #896 REGRESSION TEST, in the shape that destroyed UCL 340 / UEL 573 / UECL 20034:
        # the provider returns 200 with a rateLimit error in the body, so rows are empty and the
        # response looks successful. The key must never reach the delete.
        captured = _wire(monkeypatch, lambda *a, **k: ([], False))
        ctx = _ctx()
        sq.load_squad_players_batch(ctx, "UCL", [2026], {340})

        assert captured["load_calls"] == 0, "an incomplete fetch must not be written"
        assert captured["delete_keys"] is None, "the prior row must not be deleted"
        assert any("SKIPPED on an incomplete fetch" in e for e in ctx.errors)

    def test_partial_pagination_does_not_supersede(self, monkeypatch):
        # The APD/463 shape: NON-EMPTY but partial, because the limit hit mid-pagination and only
        # 40 of 46 players came back. An is-it-empty check cannot catch this; completeness can.
        captured = _wire(
            monkeypatch, lambda *a, **k: ([{"player": {"id": i}} for i in range(40)], False)
        )
        ctx = _ctx()
        sq.load_squad_players_batch(ctx, "APD", [2026], {463})

        assert captured["load_calls"] == 0
        assert captured["delete_keys"] is None

    def test_incomplete_key_is_not_marked_captured(self, monkeypatch):
        # Withholding the WRITE matters as much as withholding the delete. A written row marks the
        # (team, season) captured, and a historical season would then never be re-fetched, turning
        # a transient failure into a permanent hole.
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

        assert captured["delete_keys"] == ["341-2026"], "only the good key may supersede"
        written = [e["team_id"] for r in captured["rows"] for e in r["response"]]
        assert written == [341]


class TestCompleteFetchStillSupersedes:
    def test_successful_fetch_supersedes_as_before(self, monkeypatch):
        # The other half of the rule. Without this, a fix that never supersedes anything passes.
        captured = _wire(monkeypatch, lambda *a, **k: ([{"player": {"id": 7}}], True))
        ctx = _ctx()
        sq.load_squad_players_batch(ctx, "UCL", [2026], {340})

        assert captured["load_calls"] == 1
        assert captured["delete_keys"] == ["340-2026"]
        assert ctx.errors == []

    def test_empty_but_complete_response_still_supersedes(self, monkeypatch):
        # CPO decision 2026-08-03: an empty response with NO error is the provider genuinely
        # reporting no players, and is indistinguishable from one. It supersedes. Refusing to
        # supersede on emptiness would strand 3,539 historical team-seasons outside the fetch
        # cache and re-fetch them every night, about +42 min per run, permanently.
        captured = _wire(monkeypatch, lambda *a, **k: ([], True))
        sq.load_squad_players_batch(_ctx(), "UCL", [2026], {340})

        assert captured["load_calls"] == 1
        assert captured["delete_keys"] == ["340-2026"]


class TestResultIsComplete:
    """The completeness signal itself, pinned at the source."""

    @pytest.fixture(autouse=True)
    def _reset_quota(self):
        errors_quota.reset_http_quota_exhausted()
        yield
        errors_quota.reset_http_quota_exhausted()

    def test_body_level_error_is_incomplete(self, monkeypatch):
        # The per-minute limit is HTTP 200 with the error in the body, which is exactly why
        # http_client's 429 branch never fires for it.
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
        # A quota-exhausted call returns an empty body with NO errors, so the error signal alone
        # would misread it as a genuine empty. The quota flag has to be part of completeness.
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
    """Regression guard for the defect review round 1 caught.

    `fetch_merged_paged`'s returned dict is copied wholesale into the stored raw payload by
    `_merge_merged_paged` (standings, fixtures) and by the manual envelope comprehension in
    loads/teams.py, each of which excludes only a fixed key list. A new
    top-level key therefore lands in RAW_APIF_STANDINGS, RAW_APIF_TEAMS and
    RAW_APIF_FIXTURES_NEXT. The first attempt at #896 added a `complete` key here and would have
    done exactly that, with a value frozen at the first season of a multi-season merge.

    This is why completeness is a function, not a key.
    """

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
        # The exclusion is about keys WE add. Genuine provider envelope fields must still flow
        # through, because that pass-through is what the stored raw payload is built from.
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
