"""A failed fetch (HTTP 200 with the error in the body) must never be recorded as fact.

An empty response with no error stays complete and is still written.
"""

from __future__ import annotations

import types

import pytest

from ingestion.api_football import fixture_scheduling as fs
from ingestion.api_football import quota as errors_quota
from ingestion.api_football.loads import (
    player_profiles as pp,
    player_squads as psq,
    player_teams as pt,
    transfers as tr,
)


@pytest.fixture(autouse=True)
def _reset_quota():
    errors_quota.reset_http_quota_exhausted()
    yield
    errors_quota.reset_http_quota_exhausted()


def _ctx():
    return types.SimpleNamespace(
        headers={}, errors=[], client=None, add_loaded=lambda n=1: None
    )


def _rate_limited():
    """HTTP 200, error in the body, empty response: looks like a real empty one."""
    return {"response": [], "errors": {"rateLimit": "Too many requests"}, "results": 0,
            "paging": {"current": 1, "total": 1}}


def _clean_empty():
    return {"response": [], "errors": [], "results": 0, "paging": {"current": 1, "total": 1}}


# --- the three helpers report completeness ---

@pytest.mark.parametrize(
    "helper, args",
    [
        (fs.squads_response_for_team, ({}, 40)),
        (fs.profiles_response_for_player, ({}, 7)),
        (fs.player_teams_response_for_player, ({}, 7)),
    ],
    ids=["squads", "profiles", "player_teams"],
)
def test_per_entity_helpers_report_incompleteness(helper, args, monkeypatch):
    monkeypatch.setattr(fs, "fetch_merged_paged", lambda *a, **k: _rate_limited())
    rows, complete = helper(*args)
    assert rows == []
    assert complete is False, (
        f"{helper.__name__} reported a rate-limited answer as complete; the caller will store it "
        "and the key will never be fetched again"
    )


@pytest.mark.parametrize(
    "helper, args",
    [
        (fs.squads_response_for_team, ({}, 40)),
        (fs.profiles_response_for_player, ({}, 7)),
        (fs.player_teams_response_for_player, ({}, 7)),
    ],
    ids=["squads", "profiles", "player_teams"],
)
def test_empty_but_clean_response_is_still_complete(helper, args, monkeypatch):
    """An empty error-free answer is complete; refusing it would re-fetch every such key nightly."""
    monkeypatch.setattr(fs, "fetch_merged_paged", lambda *a, **k: _clean_empty())
    rows, complete = helper(*args)
    assert rows == []
    assert complete is True


# --- the three loaders must withhold the entry, not merely the write ---

def test_squads_incomplete_team_is_not_recorded(monkeypatch):
    """The entry is withheld, not just the load: a stored empty `squad_payload` marks the team done."""
    monkeypatch.setattr(psq.errors_quota, "_http_quota_exhausted", False)
    monkeypatch.setattr(
        psq, "squads_response_for_team",
        lambda h, tid, errs, error_context="": (([], False) if tid == 10 else ([{"p": 1}], True)),
    )
    written: list = []
    # The payload is the third positional argument, so a kwargs-only recorder would capture nothing.
    monkeypatch.setattr(psq, "load_json_to_bq", lambda *a, **k: written.append(a[2]))

    ctx = _ctx()
    psq.load_player_squads_batch(ctx, "PL", {10, 11}, season=2025, require_complete=False)

    assert written, "the loader wrote nothing at all; the test is not exercising the write path"
    team_ids = [e["team_id"] for p in written for e in p["response"]]
    assert 10 not in team_ids, (
        f"team 10's rate-limited empty squad was recorded ({team_ids}); `captured_team_seasons` "
        "keys on team_id presence, so that team is now never re-fetched"
    )
    assert 11 in team_ids, "the healthy team must still be written"
    assert any("INCOMPLETE" in e for e in ctx.errors), ctx.errors


@pytest.mark.parametrize(
    "mod, helper_name, loader",
    [
        (pp, "profiles_response_for_player", "load_player_profiles_global"),
        (pt, "player_teams_response_for_player", "load_player_teams_global"),
    ],
    ids=["profiles", "player_teams"],
)
def test_player_entity_incomplete_is_not_recorded(mod, helper_name, loader, monkeypatch):
    """`_existing_player_ids` keys on `$.player_id` presence, so a stored empty bio retires it."""
    monkeypatch.setattr(mod.errors_quota, "_http_quota_exhausted", False)
    monkeypatch.setattr(mod, "players_needing", lambda *a, **k: {"PL": [7, 8]})
    monkeypatch.setattr(
        mod, helper_name,
        lambda h, pid, errs, error_context="": (([], False) if pid == 7 else ([{"x": 1}], True)),
    )
    written: list = []
    monkeypatch.setattr(mod, "load_json_to_bq", lambda *a, **k: written.append(a[2]))

    ctx = _ctx()
    getattr(mod, loader)(ctx, None)

    assert written, "the loader wrote nothing at all; the test is not exercising the write path"
    ids = [e["player_id"] for p in written for e in p["response"]]
    assert 7 not in ids, (
        f"player 7's rate-limited empty payload was recorded ({ids}); `_existing_player_ids` keys "
        "on player_id presence, so that player is never fetched again"
    )
    assert 8 in ids, "the healthy player must still be written"
    assert any("INCOMPLETE" in e for e in ctx.errors), ctx.errors


# --- transfers ---

def test_transfers_with_no_team_ids_writes_nothing(monkeypatch):
    """With an empty team set the fetch loop never runs, so `complete` would stay True."""
    written: list = []
    monkeypatch.setattr(tr, "load_json_to_bq", lambda *a, **k: written.append(k))
    monkeypatch.setattr(
        tr, "transfers_response_for_team",
        lambda *a, **k: pytest.fail("must not fetch when there are no team ids"),
    )

    ctx = _ctx()
    tr.load_transfers_batch(ctx, "BL1", set())

    assert written == [], (
        "an empty whole-league transfers snapshot was written; it becomes the latest row and "
        f"hides every stored move for that competition. wrote={written}"
    )
    assert any("no team ids" in e for e in ctx.errors), ctx.errors


def test_load_json_to_bq_requires_an_explicit_append():
    """A required `append` forces the destructive WRITE_TRUNCATE mode to be stated per call."""
    import inspect

    from ingestion.api_football.bigquery import load_json_to_bq

    param = inspect.signature(load_json_to_bq).parameters["append"]
    assert param.default is inspect.Parameter.empty, (
        "`append` has a default again. It must stay required: with a default of False a single "
        "omitted argument WRITE_TRUNCATEs a raw table for every competition at once."
    )
    assert param.kind is inspect.Parameter.KEYWORD_ONLY
