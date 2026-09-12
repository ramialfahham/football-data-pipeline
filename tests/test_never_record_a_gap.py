"""A failed fetch must never be recorded as fact (#75 MR2).

THE CLASS, and why nothing caught it. #75 was about DELETION and was at least visible once you
compared layers. This is the quieter twin: a rate-limited call returns HTTP 200 with the error in
the body, so `rows` comes back EMPTY while looking successful. The loader writes it, and the key it
names is then treated as done — forever, because every "already captured" reader keys on the mere
PRESENCE of the id:

    captured_team_seasons        reads $.team_id     over ALL rows (player_squads.py)
    _existing_player_ids         reads $.player_id   over ALL rows (player_universe.py)

So the row exists, the table grew, freshness is fine, not-null is fine, row counts went UP — and
that player has no name, no date of birth and no nationality, on the surface that also drives the
URL slug. Nothing deletes anything. There is no orphan to trip a relationship test. The only
symptom is an absence, and absences are exactly what this repo's tests do not look for.

WHAT THE FIX IS, and what it deliberately is NOT. The fix is to WITHHOLD THE WRITE when the fetch
was incomplete. It is NOT to widen what counts as complete: an EMPTY response with NO error stays
complete and is still written, by rule, because that is the provider genuinely reporting
nothing and refusing it would re-fetch 3,539 historical team-seasons nightly
forever. `test_empty_but_clean_response_is_still_complete` pins that half, without which a "fix"
that simply refuses empty answers would pass every other test here.
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
    """HTTP 200, error in the BODY, empty response — indistinguishable from a real empty."""
    return {"response": [], "errors": {"rateLimit": "Too many requests"}, "results": 0,
            "paging": {"current": 1, "total": 1}}


def _clean_empty():
    """Empty and error-free — the provider genuinely has nothing. COMPLETE by rule."""
    return {"response": [], "errors": [], "results": 0, "paging": {"current": 1, "total": 1}}


# --- the three helpers must report completeness at all, like their two siblings ---

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
    """Each returns (rows, complete) and says False on a body-level error.

    Before this, all three returned a bare list, so the caller had NOTHING to branch on — the
    information simply did not reach it. Their siblings `players_response_for_team` and
    `transfers_response_for_team` have reported it since #896.
    """
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
    """The other half of the rule, and it must not be collateral damage.

    An empty error-free answer IS complete. Without this, a "fix" that refused every empty
    response would pass the test above and quietly re-fetch thousands of keys every night.
    """
    monkeypatch.setattr(fs, "fetch_merged_paged", lambda *a, **k: _clean_empty())
    rows, complete = helper(*args)
    assert rows == []
    assert complete is True


# --- the three loaders must withhold the entry, not merely the write ---

def test_squads_incomplete_team_is_not_recorded(monkeypatch):
    """Withholding the ENTRY is the point, not withholding the load job.

    `captured_team_seasons` reads `$.team_id` presence over all rows, so a stored entry with an
    empty `squad_payload` marks the team done. Asserting only "no write happened" would pass a fix
    that still appended the entry whenever another team in the same batch succeeded.
    """
    monkeypatch.setattr(psq.errors_quota, "_http_quota_exhausted", False)
    monkeypatch.setattr(
        psq, "squads_response_for_team",
        lambda h, tid, errs, error_context="": (([], False) if tid == 10 else ([{"p": 1}], True)),
    )
    written: list = []
    # The payload is the THIRD POSITIONAL argument, so a kwargs-only recorder would capture
    # nothing and this test would pass while asserting about an empty list.
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
    """Same class, same reader: `_existing_player_ids` keys on `$.player_id` presence.

    A stored empty bio retires the player permanently — this is the one that leaves a name blank
    on a page whose URL is built from that name.
    """
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


# --- transfers: the guard its sibling already had ---

def test_transfers_with_no_team_ids_writes_nothing(monkeypatch):
    """`coaches.py:38` has `if not team_ids: return`; this loader did not.

    With an empty team set the fetch loop never runs, so `complete` stays True and an EMPTY
    whole-league payload is written as fact. `stg_apif__transfers` reads the latest row per league,
    so that empty snapshot hides the real transfer history from every model downstream — and under
    the merge-on-write this loader once carried, it deleted that history outright.
    """
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


# --- the destructive write mode must be stated, never inherited ---

def test_load_json_to_bq_requires_an_explicit_append():
    """`append` defaulted to False, i.e. WRITE_TRUNCATE, on a table shared by 45 competitions.

    One omitted keyword erased everything, with no DELETE anywhere to notice. Making it required
    means the destructive mode has to be written down at the call site. Checked on the signature
    rather than by calling it, so the test cannot be satisfied by a runtime guard that a later
    refactor drops.
    """
    import inspect

    from ingestion.api_football.bigquery import load_json_to_bq

    param = inspect.signature(load_json_to_bq).parameters["append"]
    assert param.default is inspect.Parameter.empty, (
        "`append` has a default again. It must stay required: with a default of False a single "
        "omitted argument WRITE_TRUNCATEs a raw table for every competition at once."
    )
    assert param.kind is inspect.Parameter.KEYWORD_ONLY
