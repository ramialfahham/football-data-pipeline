"""#896 for the four per-league snapshot loaders (#33 item 8a).

WHY THIS EXISTS
---------------
`transfers`, `coaches`, `standings` and `teams` each write ONE row per league, and staging reads
the latest row per `league_code`. Each used to abandon its fetch loop when the daily quota latched
and then write the partial payload as if it were whole:

    for x in ...:
        if errors_quota._http_quota_exhausted:
            break                      # loop abandoned, nothing recorded
        ...
    load_json_to_bq(..., append=True)  # partial written as if complete

Under append-only that is recoverable — the partial wins in staging but the complete prior row
survives in `raw`. Under #33 item 8b (merge-on-write keyed on `league_code`) the partial write
DELETES the complete prior row. So this is the guard that makes 8b non-destructive, and these
tests are what stop it being quietly removed again.

The failure is invisible without them: a partial snapshot is a well-formed payload. Nothing throws,
no row count looks wrong, and the pipeline reports success.

HOW THESE ARE SHAPED
--------------------
The assertion is "did the loader call its BigQuery write", via a recording double — never on log
text, which a reword defeats. Each loader gets three cases: a clean run still writes; a body-level
error on any one team/season writes nothing; a mid-loop daily-quota cut writes nothing.

THE ONE THING THESE MUST NOT OVER-ASSERT: an EMPTY response with no error is a COMPLETE answer.
About 23 of 1,265 teams genuinely have no coach on every run, which is why COACHES never gates
completeness. `test_empty_but_clean_response_still_counts_as_complete` pins that, so a future
"tighten the guard" cannot start discarding good snapshots for leagues with legitimately empty
responses.
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

# Each loader is described by (how to install a fake fetch, how to invoke it). Splitting those
# two is not tidiness — the first version folded them into one `run(ctx, monkeypatch, responses)`
# helper, and the quota-cut test then had to call it with an EMPTY response list while separately
# installing its own fetch. `run` re-patched over that fetch with one that popped from the empty
# list, so `standings` and `teams` were exercising an IndexError path, not a quota cut, and both
# passed with the guard disabled. The break-it check caught it; the tests did not.

def _patch_transfers(module, monkeypatch, fetch):
    """Patch the HTTP layer UNDER the real helper, never the helper itself.

    The first version replaced `transfers.transfers_response_for_team` with a hand-rolled
    stand-in that returned `(rows, not d.get("errors"))`. That looked equivalent and was not:
    it never ran `fixture_scheduling.py`'s real `result_is_complete(data)` — the actual #896
    guard for RAW_APIF_TRANSFERS, the 6.99 GiB table this whole change exists for — and it
    reimplemented only the body-error half, missing the latched-quota half entirely. Reverting
    the real guard to `complete = True` left the entire suite green. Found in review round 1 by
    two reviewers independently.
    """
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


# SINGLE-ITEM invocations: exactly one team / one season, so the loop body runs ONCE.
# These exist because of a masking bug, not for variety — see
# test_a_quota_cut_on_a_single_iteration_is_caught.
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
    """A per-minute rate limit is HTTP 200 with the error in the body — the shape that looks
    like success. One of these anywhere in the loop makes the league snapshot partial."""
    writes = _Writes()
    monkeypatch.setattr(module, "load_json_to_bq", writes)
    patch(module, monkeypatch, _sequence([_ok(), _errored()]))
    ctx = _ctx()

    invoke(ctx)

    assert writes.tables == [], (
        f"{name}: wrote a snapshot after a body-level provider error. That payload is partial "
        "and supersedes the stored one in staging today, and DELETES it once #33 item 8b makes "
        "the table merge-on-write (#896)."
    )
    assert any("INCOMPLETE" in e for e in ctx.errors), (
        f"{name}: discarded the snapshot without reporting it. A silent discard is how a league "
        f"goes stale unnoticed. ctx.errors={ctx.errors}"
    )


@pytest.mark.parametrize("name, module, patch, invoke, invoke_one", LOADERS, ids=[x[0] for x in LOADERS])
def test_a_mid_loop_quota_cut_discards_the_snapshot(name, module, patch, invoke, invoke_one, monkeypatch):
    """The daily quota latches: `fetch_json` short-circuits to an empty body with NO error, so
    the body-error check alone would miss it. This is the second of the two signals
    `result_is_complete` exists to combine.

    The fake returns a CLEAN payload every time and merely sets the quota flag on the first
    call — so if the loader were checking only for body errors, it would see nothing wrong.
    """
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
    """The quota half of `result_is_complete` — pinned where nothing else can supply the verdict.

    `test_a_mid_loop_quota_cut_discards_the_snapshot` above runs two iterations, and every one
    of these loaders has a PRE-EXISTING top-of-loop `if _http_quota_exhausted: break` that fires
    on the second one. `platform-reviewer` showed at round 2 that this masks the new code for all
    four loaders: drop the quota half of the new check — keep only `if data.get("errors")` — and
    those four cases still pass, because the old top-of-loop guard catches it independently.

    With exactly ONE team / ONE season the loop body runs once, so the top-of-loop check never
    gets a second iteration to fire on. The only thing that can mark the run incomplete is the
    new `result_is_complete` call, which is precisely what needs pinning: the daily quota
    short-circuits `fetch_json` to an empty body with NO error, so a body-error check alone is
    blind to it.
    """
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
    """Pin `transfers_response_for_team`'s OWN completeness signal, directly.

    The loader-level tests above reach this function through `load_transfers_batch`, and
    `load_transfers_batch` has a pre-existing per-iteration quota check of its own. Two
    reviewers showed round 1's transfers cases could pass on THAT check while this function's
    new `result_is_complete` call was reverted — right answer, wrong code path. This test calls
    the helper directly, so nothing else can supply the verdict for it.
    """
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
    """An empty response with NO error is a COMPLETE answer and must still be written.

    Measured 2026-07-30..08-03: ~23 of 1,265 teams genuinely have no coach on every run, which
    is why COACHES is reported and never gates. If the guard treated "empty" as "incomplete",
    those leagues would stop being written entirely — trading one silent failure for another.
    """
    writes = _Writes()
    monkeypatch.setattr(coaches, "load_json_to_bq", writes)
    _patch_fetch(coaches, monkeypatch, lambda: _ok(response=[]))
    ctx = _ctx()

    coaches.load_coaches(ctx, "BL1", {1, 2})

    assert len(writes.tables) == 1, (
        "an empty-but-clean response was treated as incomplete. Emptiness is a legitimate "
        "answer; only a body error or the latched quota flag means partial."
    )
