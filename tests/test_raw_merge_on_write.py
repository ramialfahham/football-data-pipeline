"""Raw appends and NEVER deletes — the merge-on-write is gone (CPO 2026-08-17).

WHAT THIS FILE IS NOW
---------------------
It was the file that pinned #33 item 8b: three loaders had to append a whole-league snapshot
and then DELETE that league's older rows. It now pins the opposite, because the CPO reversed
that decision after two independent assessments found the same root cause.

The reversal in one sentence: the delete fired whenever a fetch was judged COMPLETE, and
"complete" means only that the call did not error — `http_client.result_is_complete` counts an
empty error-free response as complete, deliberately (CPO 2026-08-03). So a provider answering
with nothing, or with less than it gave us yesterday, destroyed the stored history past the
7-day time-travel window with no signal anywhere. Measured damage before the reversal: 29
events across 5 fixtures (`escalations.log` 2026-08-17) and four squads on 2026-08-02
(`squads.py`). Retention is now base's decision, which is where the layer model always put it.

Do NOT restore a delete here to "bound the table". The scan-cost argument that bought it is
spent: staging became a stored table on 2026-08-13, so each raw table is parsed once a night
rather than once per test. If growth ever needs bounding, it is compaction by version count,
never a delete at write time, and never keyed on time (biennial competitions lose their only
row — #892).

HOW THESE ARE SHAPED
--------------------
Each loader runs for real against a client double that records every query it issues. Nothing
about the loader is monkeypatched except `load_json_to_bq`, because a real BigQuery load is not
the subject. A DELETE cannot reach BigQuery except through `client.query`, so asserting that no
query is issued at all catches a re-introduction under ANY name — which a source grep or an
attribute check would not.

That matters here specifically: the deleted helpers were reachable three different ways (a
shared helper in `bigquery.py`, a private per-key one in `squads.py`, a private per-fixture one
in `batch_fixtures.py`). Pinning the names would pin the three that existed, not the fourth
someone writes next.
"""

from __future__ import annotations

import types

import pytest

from ingestion.api_football import fixture_scheduling
from ingestion.api_football import quota as errors_quota
from ingestion.api_football.loads import coaches, squads, standings, teams, transfers


class _Client:
    """Records every query the loader issues. Any DML at all is a failure here."""

    def __init__(self):
        self.queries: list[tuple[str, object]] = []

    def query(self, sql, job_config=None):
        self.queries.append((sql, job_config))
        return types.SimpleNamespace(result=lambda: None)

    def dml(self) -> list[str]:
        return [
            sql
            for sql, _ in self.queries
            if any(k in sql.lower() for k in ("delete", "update", "merge", "truncate"))
        ]


class _Writes:
    """Records every raw write, keeping the kwargs so `append=True` can be asserted."""

    def __init__(self):
        self.calls: list[tuple[str, dict]] = []

    def __call__(self, client, table, payload, **kwargs):
        self.calls.append((table, kwargs))


def _ctx(client):
    return types.SimpleNamespace(
        client=client, headers={}, errors=[], tables_loaded=0,
        add_loaded=lambda n=1: None,
    )


def _ok():
    return {"response": [{"team": {"id": 1}}], "errors": [], "results": 1,
            "paging": {"current": 1, "total": 1}}


def _errored():
    """The per-minute rate limit shape: HTTP 200, error in the BODY, response empty."""
    return {"response": [], "errors": {"rateLimit": "Too many requests"}, "results": 0,
            "paging": {"current": 1, "total": 1}}


@pytest.fixture(autouse=True)
def _reset_quota():
    errors_quota.reset_http_quota_exhausted()
    yield
    errors_quota.reset_http_quota_exhausted()


# `transfers` reaches the provider through fixture_scheduling, the other two through their
# own module namespace. Patching the HTTP layer UNDER the real helper (never the helper
# itself) is what makes the real #896 guard run.
def _patch_transfers(monkeypatch, fetch):
    monkeypatch.setattr(fixture_scheduling, "fetch_merged_paged", lambda *a, **k: fetch())


def _patch_standings(monkeypatch, fetch):
    monkeypatch.setattr(standings, "fetch_merged_paged", lambda *a, **k: fetch())


def _patch_teams(monkeypatch, fetch):
    monkeypatch.setattr(teams, "fetch_merged_paged", lambda *a, **k: fetch())


def _invoke_transfers(ctx):
    transfers.load_transfers_batch(ctx, "BL1", {1})


def _invoke_standings(ctx):
    standings.load_standings_if_enabled(ctx, "BL1", 78, [2025], {"standings": True})


def _invoke_teams(ctx):
    teams.load_teams_merge_and_extend_ids(ctx, "BL1", 78, [2025], 2025, set())


WHOLE_LEAGUE = [
    ("transfers", transfers, _patch_transfers, _invoke_transfers, "RAW_APIF_TRANSFERS"),
    ("standings", standings, _patch_standings, _invoke_standings, "RAW_APIF_STANDINGS"),
    ("teams", teams, _patch_teams, _invoke_teams, "RAW_APIF_TEAMS"),
]
IDS = [x[0] for x in WHOLE_LEAGUE]


@pytest.mark.parametrize("name, module, patch, invoke, table", WHOLE_LEAGUE, ids=IDS)
def test_a_clean_run_appends_and_issues_no_dml(
    name, module, patch, invoke, table, monkeypatch
):
    """THE case this file exists for, in its new direction.

    A clean, complete fetch writes its snapshot and touches nothing else. Before the reversal
    this same run deleted every older row for the league. The older rows are now what makes a
    later shrunken answer survivable, so any DML at all here is the defect.
    """
    writes = _Writes()
    client = _Client()
    monkeypatch.setattr(module, "load_json_to_bq", writes)
    patch(monkeypatch, lambda: _ok())

    invoke(_ctx(client))

    assert [t for t, _ in writes.calls] == [table], (
        f"{name}: expected exactly one write to {table}, got {[t for t, _ in writes.calls]}"
    )
    assert client.dml() == [], (
        f"{name}: issued DML against raw. Raw appends and never deletes (CPO 2026-08-17) — "
        f"the older rows are the only copy of anything a later answer drops. SQL={client.dml()}"
    )


@pytest.mark.parametrize("name, module, patch, invoke, table", WHOLE_LEAGUE, ids=IDS)
def test_every_raw_write_is_an_append(
    name, module, patch, invoke, table, monkeypatch
):
    """The other half of "never deletes", and it needs its own assertion.

    A loader that passed `append=False` would reach WRITE_TRUNCATE (`bigquery.py`, where
    `append` defaults to False), which destroys the whole table's history for every
    competition at once while issuing no DELETE — so the test above would stay green.
    """
    writes = _Writes()
    client = _Client()
    monkeypatch.setattr(module, "load_json_to_bq", writes)
    patch(monkeypatch, lambda: _ok())

    invoke(_ctx(client))

    _, kwargs = writes.calls[0]
    assert kwargs.get("append") is True, (
        f"{name}: wrote with append={kwargs.get('append')!r}. Anything but True is "
        "WRITE_TRUNCATE, which erases every competition's rows in that table."
    )


@pytest.mark.parametrize("name, module, patch, invoke, table", WHOLE_LEAGUE, ids=IDS)
def test_an_incomplete_fetch_writes_nothing(
    name, module, patch, invoke, table, monkeypatch
):
    """#896, unchanged by the reversal and deliberately kept.

    Append-only makes a partial write recoverable rather than fatal, which is exactly why it
    would be tempting to drop this guard. Do not: a known-partial payload put in front of base
    is a worse row for no reason, and the run would report the fixture as touched when it was
    not. Nothing here was loosened.
    """
    writes = _Writes()
    client = _Client()
    monkeypatch.setattr(module, "load_json_to_bq", writes)
    patch(monkeypatch, lambda: _errored())

    ctx = _ctx(client)
    invoke(ctx)

    assert writes.calls == [], f"{name}: wrote a partial snapshot (#896)."
    assert client.dml() == [], f"{name}: issued DML on the incomplete-fetch path."
    assert any("INCOMPLETE" in e for e in ctx.errors), (
        f"{name}: discarded silently. ctx.errors={ctx.errors}"
    )


def test_the_players_loader_appends_and_deletes_nothing(monkeypatch):
    """RAW_APIF_PLAYERS had the best-shaped delete in the codebase and still lost data.

    It was keyed per (team, season) rather than per league, so a quota cut left un-fetched
    keys alone — genuinely careful. It did not help: an empty error-free /players response is
    a COMPLETE answer, so it superseded the roster it could not replace, and on 2026-08-02
    UCL 340 went 25 players to 0. Correct grain does not rescue a delete whose trigger cannot
    tell "no players" from "we lost the players".
    """
    client = _Client()
    monkeypatch.setattr(squads.errors_quota, "_http_quota_exhausted", False)
    monkeypatch.setattr(squads, "captured_player_team_seasons", lambda ctx: set())
    monkeypatch.setattr(
        squads, "players_response_for_team", lambda *a, **k: ([{"player": {"id": 7}}], True)
    )
    written: list = []
    monkeypatch.setattr(
        squads,
        "load_json_payload_rows_to_bq",
        lambda client_, table, rows, **kw: (written.append((table, kw)), len(rows))[1],
    )

    squads.load_squad_players_batch(_ctx(client), "UCL", [2026], {340})

    assert [t for t, _ in written] == ["RAW_APIF_PLAYERS"], (
        f"the loader did not write; the test is not exercising it. wrote={written}"
    )
    assert written[0][1].get("append") is True, "RAW_APIF_PLAYERS must be appended, not truncated"
    assert client.dml() == [], (
        f"the players loader issued DML against raw: {client.dml()}. The per-(team, season) "
        "delete was removed 2026-08-17 and must not come back."
    )


def test_an_incomplete_fetch_still_extends_team_ids(monkeypatch):
    """Narrowed survivor of `test_a_failed_delete_still_extends_team_ids`.

    That test protected the id extension from a failing DELETE. There is no delete any more,
    so the case is gone — but the property it guarded is not: `teams.py` states the extension
    runs EITHER WAY, deliberately, because `coaches`, `transfers` and `squads` all fetch by
    team id downstream. Re-pointed at the path that still exists, the discarded-snapshot one.
    Deleting the test outright would have dropped a live guarantee along with a dead case.
    """
    writes = _Writes()
    client = _Client()
    monkeypatch.setattr(teams, "load_json_to_bq", writes)
    # Incomplete (body error) but NOT empty: teams came back, the snapshot is still refused.
    _patch_teams(monkeypatch, lambda: {
        "response": [{"team": {"id": 1}}],
        "errors": {"rateLimit": "Too many requests"},
        "results": 1,
        "paging": {"current": 1, "total": 1},
    })
    team_ids: set[int] = set()

    ctx = _ctx(client)
    teams.load_teams_merge_and_extend_ids(ctx, "BL1", 78, [2025], 2025, team_ids)

    assert writes.calls == [], "an incomplete snapshot must not be written (#896)"
    assert team_ids == {1}, (
        f"a discarded snapshot cost the run its team ids (got {team_ids}); the id extension "
        "is not a write to raw and must be independent of it, or one short season becomes a "
        "run-wide outage for coaches, transfers and squads."
    )


def test_no_loader_module_carries_a_delete_helper():
    """Pins the removal against a delete being reintroduced quietly, under any of its names.

    Checks the runtime namespace of every module in `loads/` plus `bigquery` itself, so a
    comment mentioning a helper cannot satisfy it and a re-import would be caught. The
    behavioural tests above are the real guard — this one names the three that existed so the
    failure message tells the next person what was removed and why.
    """
    import importlib
    import pkgutil

    from ingestion.api_football import bigquery as bq_module
    from ingestion.api_football import loads

    banned = (
        "delete_superseded_league_rows",
        "_delete_superseded_player_rows",
        "_delete_fixtures",
    )
    offenders: list[str] = []
    for mod in pkgutil.iter_modules(loads.__path__):
        module = importlib.import_module(f"{loads.__name__}.{mod.name}")
        offenders += [f"loads.{mod.name}.{n}" for n in banned if hasattr(module, n)]
    offenders += [f"bigquery.{n}" for n in banned if hasattr(bq_module, n)]

    assert offenders == [], (
        f"a raw delete helper is back: {offenders}. Raw appends and never deletes "
        "(CPO 2026-08-17, reversing #33 item 8b). If the table needs bounding, compact by "
        "version count in a separate job — never delete at write time, and never key it on "
        "time (#892: biennial competitions lose their only row)."
    )


def test_coaches_was_never_a_merge_loader_and_still_is_not(monkeypatch):
    """`coaches` is the loader that looks most like the three above and never merged.

    Kept from the original file, inverted in meaning: it used to prove the converted set
    excluded coaches, and now proves the set is empty. `stg_apif__coaches` reads ALL snapshots
    by CPO ruling (escalations.log, 2026-06-23) to preserve every coach ever seen — the same
    reasoning that has now been applied to every other table.
    """
    writes = _Writes()
    client = _Client()
    monkeypatch.setattr(coaches, "load_json_to_bq", writes)
    monkeypatch.setattr(coaches, "fetch_merged_paged", lambda *a, **k: _ok())

    coaches.load_coaches(_ctx(client), "BL1", {1})

    assert [t for t, _ in writes.calls] == ["RAW_APIF_COACHES"], (
        "coaches did not write its snapshot; the test is not exercising the loader."
    )
    assert client.dml() == [], f"COACHES issued DML against raw: {client.dml()}"
