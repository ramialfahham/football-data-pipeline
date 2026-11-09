"""Tests that the transfers, coaches, standings and teams loaders write no snapshot from a partial fetch.

An empty response with no error is a complete answer and must not be treated as partial.
"""

from __future__ import annotations

import types

import pytest

from ingestion.api_football import fixture_scheduling
from ingestion.api_football import quota as errors_quota
from ingestion.api_football.loads import coaches, standings, teams, transfers


class _Writes:
    """Records every raw write a loader attempts."""

    def __init__(self):
        self.tables: list[str] = []

    def __call__(self, client, table, payload, **kwargs):
        self.tables.append(table)


def _ctx():
    return types.SimpleNamespace(
        client=object(), headers={}, errors=[], tables_loaded=0,
        add_loaded=lambda n=1: None,
    )


def _ok(response=None):
    """A clean provider response: no body-level errors."""
    return {"response": response if response is not None else [{"team": {"id": 1}}],
            "errors": [], "results": 1, "paging": {"current": 1, "total": 1}}


def _errored():
    """The per-minute rate limit shape: HTTP 200, error in the BODY, response empty."""
    return {"response": [], "errors": {"rateLimit": "Too many requests"},
            "results": 0, "paging": {"current": 1, "total": 1}}


@pytest.fixture(autouse=True)
def _reset_quota():
    errors_quota.reset_http_quota_exhausted()
    yield
    errors_quota.reset_http_quota_exhausted()


# --- the four loaders, driven through a common table of how each is invoked ---

# Installing the fake fetch and invoking the loader are separate steps so a test's own fetch is never re-patched.

def _patch_transfers(module, monkeypatch, fetch):
    """Patch the HTTP layer under the real helper so its real `result_is_complete` check runs."""
    monkeypatch.setattr(fixture_scheduling, "fetch_merged_paged", lambda *a, **k: fetch())


def _patch_fetch(module, monkeypatch, fetch):
    monkeypatch.setattr(module, "fetch_merged_paged", lambda *a, **k: fetch())


def _invoke_transfers(ctx):
    transfers.load_transfers_batch(ctx, "BL1", {1, 2})


def _invoke_coaches(ctx):
    coaches.load_coaches(ctx, "BL1", {1, 2})


def _invoke_standings(ctx):
    standings.load_standings_if_enabled(ctx, "BL1", 78, [2024, 2025], {"standings": True})


def _invoke_teams(ctx):
    teams.load_teams_merge_and_extend_ids(ctx, "BL1", 78, [2024, 2025], 2025, set())


# Single-item invocations: one team or season, so the loop body runs once.
def _invoke_transfers_one(ctx):
    transfers.load_transfers_batch(ctx, "BL1", {1})


def _invoke_coaches_one(ctx):
    coaches.load_coaches(ctx, "BL1", {1})


def _invoke_standings_one(ctx):
    standings.load_standings_if_enabled(ctx, "BL1", 78, [2025], {"standings": True})


def _invoke_teams_one(ctx):
    teams.load_teams_merge_and_extend_ids(ctx, "BL1", 78, [2025], 2025, set())


LOADERS = [
    ("transfers", transfers, _patch_transfers, _invoke_transfers, _invoke_transfers_one),
    ("coaches", coaches, _patch_fetch, _invoke_coaches, _invoke_coaches_one),
    ("standings", standings, _patch_fetch, _invoke_standings, _invoke_standings_one),
    ("teams", teams, _patch_fetch, _invoke_teams, _invoke_teams_one),
]


def _sequence(responses):
    """A fetch that returns each response in turn. Two fetches per loader in these tests."""
    seq = list(responses)
    return lambda: seq.pop(0)


@pytest.mark.parametrize("name, module, patch, invoke, invoke_one", LOADERS, ids=[x[0] for x in LOADERS])
def test_a_clean_run_still_writes(name, module, patch, invoke, invoke_one, monkeypatch):
    """The guard must not cost a normal run its snapshot."""
    writes = _Writes()
    monkeypatch.setattr(module, "load_json_to_bq", writes)
    patch(module, monkeypatch, _sequence([_ok(), _ok()]))
    ctx = _ctx()

    invoke(ctx)

    assert len(writes.tables) == 1, (
        f"{name}: a clean run wrote {len(writes.tables)} payloads, expected exactly 1. The #896 "
        "guard must only suppress INCOMPLETE snapshots."
    )


@pytest.mark.parametrize("name, module, patch, invoke, invoke_one", LOADERS, ids=[x[0] for x in LOADERS])
def test_a_body_level_error_discards_the_snapshot(name, module, patch, invoke, invoke_one, monkeypatch):
    """A per-minute rate limit is HTTP 200 with the error in the body, so it looks like success."""
    writes = _Writes()
    monkeypatch.setattr(module, "load_json_to_bq", writes)
    patch(module, monkeypatch, _sequence([_ok(), _errored()]))
    ctx = _ctx()

    invoke(ctx)

    assert writes.tables == [], (
        f"{name}: wrote a snapshot after a body-level provider error. That payload is partial "
        "and supersedes the stored one in staging, which reads latest-per-league — so every "
        "model downstream serves the short version until the next good run (#896)."
    )
    assert any("INCOMPLETE" in e for e in ctx.errors), (
        f"{name}: discarded the snapshot without reporting it. A silent discard is how a league "
        f"goes stale unnoticed. ctx.errors={ctx.errors}"
    )


@pytest.mark.parametrize("name, module, patch, invoke, invoke_one", LOADERS, ids=[x[0] for x in LOADERS])
def test_a_mid_loop_quota_cut_discards_the_snapshot(name, module, patch, invoke, invoke_one, monkeypatch):
    """A latched daily quota yields an empty body with no error, so a body-error check alone misses it."""
    writes = _Writes()
    monkeypatch.setattr(module, "load_json_to_bq", writes)

    def _sets_quota_then_ok():
        errors_quota._http_quota_exhausted = True
        return _ok()

    patch(module, monkeypatch, _sets_quota_then_ok)
    ctx = _ctx()

    invoke(ctx)

    assert writes.tables == [], (
        f"{name}: wrote a snapshot after the daily quota cut the loop short. The remaining "
        "teams/seasons were never fetched, so the payload is partial (#896)."
    )


@pytest.mark.parametrize(
    "name, module, patch, invoke, invoke_one", LOADERS, ids=[x[0] for x in LOADERS]
)
def test_a_quota_cut_on_a_single_iteration_is_caught(
    name, module, patch, invoke, invoke_one, monkeypatch
):
    """With one item the top-of-loop quota break never fires, so only `result_is_complete` can mark it partial."""
    writes = _Writes()
    monkeypatch.setattr(module, "load_json_to_bq", writes)

    def _sets_quota_then_ok():
        errors_quota._http_quota_exhausted = True
        return _ok()

    patch(module, monkeypatch, _sets_quota_then_ok)
    ctx = _ctx()

    invoke_one(ctx)

    assert writes.tables == [], (
        f"{name}: wrote a snapshot when the daily quota latched during its ONLY fetch. Nothing "
        "else can catch this — there is no second iteration for the pre-existing top-of-loop "
        "check to fire on — so the new result_is_complete call is not doing its job, or is only "
        "looking at body-level errors and is blind to the quota flag (#896)."
    )


@pytest.mark.parametrize(
    "payload, expected_complete",
    [(_ok(), True), (_errored(), False)],
    ids=["clean", "body-error"],
)
def test_transfers_helper_reports_completeness_itself(payload, expected_complete, monkeypatch):
    """Called directly, so the loader's own per-iteration quota check cannot supply the verdict."""
    monkeypatch.setattr(fixture_scheduling, "fetch_merged_paged", lambda *a, **k: payload)

    rows, complete = fixture_scheduling.transfers_response_for_team({}, 1, [])

    assert complete is expected_complete, (
        "transfers_response_for_team returned complete="
        f"{complete} for a {'clean' if expected_complete else 'body-errored'} response. This "
        "is the signal load_transfers_batch uses to decide whether a snapshot may supersede "
        "6.99 GiB of stored transfers (#896)."
    )
    assert rows == list(payload.get("response") or [])


def test_empty_but_clean_response_still_counts_as_complete(monkeypatch):
    """An empty response with no error is complete, as some teams genuinely have no coach."""
    writes = _Writes()
    monkeypatch.setattr(coaches, "load_json_to_bq", writes)
    _patch_fetch(coaches, monkeypatch, lambda: _ok(response=[]))
    ctx = _ctx()

    coaches.load_coaches(ctx, "BL1", {1, 2})

    assert len(writes.tables) == 1, (
        "an empty-but-clean response was treated as incomplete. Emptiness is a legitimate "
        "answer; only a body error or the latched quota flag means partial."
    )
