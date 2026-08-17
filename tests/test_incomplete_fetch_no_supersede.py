"""An incomplete fetch must never be written (#896).

The original defect: `_delete_superseded_player_rows` deleted the prior row for a (team, season)
keyed on what the NEW row claimed, with no check that the fetch had succeeded. A per-minute rate
limit arrives as HTTP 200 with the error in the body, so a rejected call looked like an
empty-but-valid squad and destroyed the good rows it failed to replace. Measured on the 2026-08-02
nightly: UCL 340 went 25 players to 0, UEL 573 24 to 0, UECL 20034 23 to 0, and APD 463 46 to 40
when the limit hit mid-pagination.

No existing test could catch this class and none could be written against the old signals: the
TABLE GREW while the data was destroyed, so row-count, freshness and not-null checks all passed.

⚠ THE DELETES ARE GONE since 2026-08-17 (CPO: raw appends and never deletes; the removal is pinned
by `tests/test_raw_merge_on_write.py`). This file keeps its subject anyway, narrowed to the half
that still exists and still matters: an incomplete fetch is not WRITTEN. That is not the same
guarantee as "not deleted", and it is not made redundant by append-only — a written row marks the
key captured, so a rate-limited empty answer would still turn a transient failure into a permanent
hole that no later run re-fetches.

These tests pin both halves of the rule, because pinning only the refusal would let a fix that
never writes anything pass.
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
        # THE #896 REGRESSION TEST, in the shape that destroyed UCL 340 / UEL 573 / UECL 20034:
        # the provider returns 200 with a rateLimit error in the body, so rows are empty and the
        # response looks successful. The key must never reach the delete.
        captured = _wire(monkeypatch, lambda *a, **k: ([], False))
        ctx = _ctx()
        sq.load_squad_players_batch(ctx, "UCL", [2026], {340})

        assert captured["load_calls"] == 0, "an incomplete fetch must not be written"
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

        assert captured["keys"] == ["341-2026"], "only the good key may be written"
        written = [e["team_id"] for r in captured["rows"] for e in r["response"]]
        assert written == [341]


class TestCompleteFetchIsStillWritten:
    def test_successful_fetch_is_written_as_before(self, monkeypatch):
        # The other half of the rule. Without this, a fix that never writes anything passes.
        captured = _wire(monkeypatch, lambda *a, **k: ([{"player": {"id": 7}}], True))
        ctx = _ctx()
        sq.load_squad_players_batch(ctx, "UCL", [2026], {340})

        assert captured["load_calls"] == 1
        assert captured["keys"] == ["340-2026"]
        assert ctx.errors == []

    def test_empty_but_complete_response_is_still_written(self, monkeypatch):
        # CPO decision 2026-08-03: an empty response with NO error is the provider genuinely
        # reporting no players, and is indistinguishable from one. It is written. Refusing to
        # write on emptiness would strand 3,539 historical team-seasons outside the fetch
        # cache and re-fetch them every night, about +42 min per run, permanently.
        #
        # ⚠ This is the exact case that made the delete lethal, and it is why the answer was to
        # remove the delete rather than to narrow this rule: the empty answer still lands, but
        # the fuller earlier row is still there for base to prefer. Do not "fix" this by
        # refusing empty responses — that trades a data loss for a quota bill and was measured.
        captured = _wire(monkeypatch, lambda *a, **k: ([], True))
        sq.load_squad_players_batch(_ctx(), "UCL", [2026], {340})

        assert captured["load_calls"] == 1
        # The row IS written, carrying the key with an empty players_payload. That is the point:
        # the key counts as captured so it is not re-fetched nightly.
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
    """Run the REAL _fetch_and_persist_batch with no network and no BigQuery.

    `_delete_fixtures` is deliberately NOT stubbed, because it no longer exists. Any DML would
    now have to travel through `ctx.client.query`, so the recording client catches a delete
    reintroduced under any name — which patching a known helper never could.
    """
    captured: dict = {"inserted": None}

    monkeypatch.setattr(bf.errors_quota, "_http_quota_exhausted", False)
    monkeypatch.setattr(bf, "fetch_json", lambda *a, **k: data)
    monkeypatch.setattr(bf, "ensure_unified_raw_table", lambda *a, **k: None)
    monkeypatch.setattr(bf, "_fixture_details_table_id", lambda: "p.raw.FIXTURE_DETAILS")
    monkeypatch.setattr(
        bf,
        "_insert_fixture_rows",
        lambda client, table_name, response, ts, league_code: captured.__setitem__(
            "inserted", [r["fixture"]["id"] for r in response]
        ),
    )
    return captured


class TestFixtureDetailsRetryKeepsBothVersions:
    """The fixture-details half of the append-only ruling (GitLab #75).

    This table is the one that cost real data. Its row bundles lineups, events, statistics and
    player stats TOGETHER, so a retry chasing late statistics could return richer in one section
    and poorer in another. The delete made the poorer answer the only surviving one: fixture
    1564795 went 27 events to 17, an entire penalty shootout, unrecoverable.

    CPO 2026-08-17, verbatim: "raw keeps both versions." Base decides, using the rule it already
    has (`base_apif__fixture_events`, newest per (league_code, fixture_id, event_index)).
    """

    def test_a_retried_fixture_is_appended_and_nothing_is_deleted(self, monkeypatch):
        # THE case the ruling exists for. 111 was retried (previously empty statistics) and the
        # provider answered cleanly. Before the reversal this deleted the stored payload first.
        # Now the new version is appended alongside the old one.
        #
        # 222 was also retried and NOT returned. Under the old code that omission needed its own
        # special case, or its stored row was superseded with nothing. Append-only removes the
        # case rather than guarding it: an id the provider skipped is simply not written.
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
        # #896, unchanged and still needed. Not written with an EMPTY response on purpose: an
        # empty body returns early at `if not response` even unguarded, so a test built that way
        # would pass for the wrong reason and prove nothing (this repo has shipped three such
        # tests — #63). Here the batch is PARTIAL: 111 came back, 222 did not, and the per-minute
        # limit is reported in the body. The whole batch is discarded and retried next run.
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
        # "Both versions land" is TWO properties: no delete, and an APPEND. A write disposition
        # flipped to WRITE_TRUNCATE would destroy every fixture in the table for every
        # competition while issuing no DELETE at all, and the two tests above would stay green.
        # Exercises the REAL `_insert_fixture_rows`; only the BigQuery load job is doubled.
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
