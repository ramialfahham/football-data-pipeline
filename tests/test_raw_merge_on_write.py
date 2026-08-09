"""Merge-on-write for the three whole-league snapshot tables (#33 item 8b).

WHY THIS EXISTS
---------------
`TRANSFERS`, `STANDINGS` and `TEAMS` each write ONE row covering the entire league, and
staging reads only the latest row per `league_code`. Every earlier row is therefore dead
weight that is still scanned — `RAW_APIF_TRANSFERS` was 1,143 rows / 6.99 GiB on
2026-08-09, 59% of all raw, and the two most expensive nodes in the warehouse were both
scans of a view over it. Each run now appends its snapshot and deletes that league's
strictly-older rows.

The whole change rests on ONE invariant: the delete boundary is the appended row's OWN
`ingested_at`, so `ingested_at < @before` can never reach the row just written. Get that
wrong and the loader deletes everything including its own write, leaving the league empty.
`test_the_delete_boundary_is_the_write_s_own_timestamp` is the case that pins it.

HOW THESE ARE SHAPED
--------------------
The delete is asserted through the REAL `delete_superseded_league_rows` against a fake
client that records SQL and query parameters. It is deliberately NOT monkeypatched.

That is not a style choice. `tests/test_squad_players_rows.py` monkeypatches
`_delete_superseded_player_rows` — the sibling merge helper — so the SQL it builds and the
parameters it binds are asserted nowhere, and reverting its `ingested_at` bound leaves that
suite green. Ten decoration tests have now been caught in this repo by breaking the subject
rather than reading the test; monkeypatching the very helper under test was one of the named
causes. Only `load_json_to_bq` is doubled here, because a real BigQuery load is not the
subject.

WHAT MUST NOT BE ADDED TO THE CONVERTED SET
-------------------------------------------
`test_only_the_three_whole_league_loaders_merge` pins the set. Two exclusions are data
destruction, not preference:

  COACHES — `stg_apif__coaches.sql` reads ALL snapshots by CPO ruling (escalations.log,
  2026-06-23) to preserve every coach ever seen. A league-keyed delete destroys ~120 coaches
  whose teams left our pull. It is the loader that looks most like the three converted ones,
  which is exactly why it is pinned here.

  SQUADS — the loader writes a team SUBSET (see #37; WCQAF exposes 10 of 44 teams today).
  Merge-on-write would make a recoverable staging bug permanent.

PLAYER_PROFILES and PLAYER_TEAMS accumulate per player and must NEVER be converted.
"""

from __future__ import annotations

import types

import pytest

from ingestion.api_football import fixture_scheduling
from ingestion.api_football import quota as errors_quota
from ingestion.api_football.loads import coaches, standings, teams, transfers


class _Client:
    """Records every query the loader issues. `fail=True` makes the DELETE raise."""

    def __init__(self, fail: bool = False):
        self.queries: list[tuple[str, object]] = []
        self._fail = fail

    def query(self, sql, job_config=None):
        self.queries.append((sql, job_config))
        if self._fail:
            raise RuntimeError("simulated BigQuery DML failure")
        return types.SimpleNamespace(result=lambda: None)

    def deletes(self) -> list[tuple[str, object]]:
        return [(sql, jc) for sql, jc in self.queries if "delete from" in sql.lower()]


class _Writes:
    """Records every raw write, keeping the kwargs so `ingested_at` can be compared."""

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
# itself) is what makes the real #896 guard run — see test_incomplete_snapshot_not_written.
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


CONVERTED = [
    ("transfers", transfers, _patch_transfers, _invoke_transfers, "RAW_APIF_TRANSFERS"),
    ("standings", standings, _patch_standings, _invoke_standings, "RAW_APIF_STANDINGS"),
    ("teams", teams, _patch_teams, _invoke_teams, "RAW_APIF_TEAMS"),
]
IDS = [x[0] for x in CONVERTED]


def _params(job_config) -> dict:
    return {p.name: p.value for p in job_config.query_parameters}


@pytest.mark.parametrize("name, module, patch, invoke, table", CONVERTED, ids=IDS)
def test_a_clean_run_appends_then_deletes_the_superseded_rows(
    name, module, patch, invoke, table, monkeypatch
):
    """One write, then exactly one DELETE against the same table."""
    writes = _Writes()
    client = _Client()
    monkeypatch.setattr(module, "load_json_to_bq", writes)
    patch(monkeypatch, lambda: _ok())

    invoke(_ctx(client))

    assert [t for t, _ in writes.calls] == [table], (
        f"{name}: expected exactly one write to {table}, got {[t for t, _ in writes.calls]}"
    )
    deletes = client.deletes()
    assert len(deletes) == 1, (
        f"{name}: expected exactly one DELETE after the append, got {len(deletes)}. "
        "Without it the table keeps growing with competitions x runs (#33 item 8b)."
    )
    assert table in deletes[0][0], (
        f"{name}: the DELETE does not target {table}. SQL={deletes[0][0]!r}"
    )


@pytest.mark.parametrize("name, module, patch, invoke, table", CONVERTED, ids=IDS)
def test_the_delete_is_scoped_to_this_league(
    name, module, patch, invoke, table, monkeypatch
):
    """`league_code` is bound as a parameter, so one competition can never delete another's
    rows. All 45 competitions share one physical table."""
    writes = _Writes()
    client = _Client()
    monkeypatch.setattr(module, "load_json_to_bq", writes)
    patch(monkeypatch, lambda: _ok())

    invoke(_ctx(client))

    sql, job_config = client.deletes()[0]
    assert "league_code = @lc" in sql, (
        f"{name}: the DELETE is not scoped to a league. SQL={sql!r}. An unscoped delete "
        "wipes every other competition's snapshot from the shared table."
    )
    assert _params(job_config)["lc"] == "BL1", (
        f"{name}: the DELETE bound league_code={_params(job_config).get('lc')!r}, expected 'BL1'."
    )


@pytest.mark.parametrize("name, module, patch, invoke, table", CONVERTED, ids=IDS)
def test_the_delete_boundary_is_the_write_s_own_timestamp(
    name, module, patch, invoke, table, monkeypatch
):
    """THE case this file exists for.

    The delete must be bounded strictly BEFORE the `ingested_at` of the row just appended.
    Same value, strict `<`: older rows go, the new row stays. If the bound were dropped, or
    computed independently of the write, the loader would delete its own snapshot and leave
    the league with no row at all — and staging, which reads the latest row per league,
    would then serve nothing for that competition.
    """
    writes = _Writes()
    client = _Client()
    monkeypatch.setattr(module, "load_json_to_bq", writes)
    patch(monkeypatch, lambda: _ok())

    invoke(_ctx(client))

    written_stamp = writes.calls[0][1].get("ingested_at")
    assert written_stamp is not None, (
        f"{name}: the loader did not pass `ingested_at` to the write, so the delete boundary "
        "cannot be the row's own timestamp — it would be an independently-taken clock reading."
    )

    sql, job_config = client.deletes()[0]
    assert "ingested_at < @before" in sql, (
        f"{name}: the DELETE has no strict upper bound on ingested_at. SQL={sql!r}. Without "
        "it the statement also deletes the row this run just wrote."
    )
    assert _params(job_config)["before"].isoformat() == written_stamp, (
        f"{name}: the delete boundary {_params(job_config)['before'].isoformat()!r} is not the "
        f"written row's stamp {written_stamp!r}. Any drift here deletes the new row or spares "
        "a superseded one."
    )


@pytest.mark.parametrize("name, module, patch, invoke, table", CONVERTED, ids=IDS)
def test_an_incomplete_fetch_deletes_nothing(
    name, module, patch, invoke, table, monkeypatch
):
    """The 8a guard returns before the write, so the delete must be unreachable.

    This is the ordering that makes 8b safe: a partial snapshot that reached the delete
    would remove the good stored row and replace it with less data — permanently, past the
    7-day time-travel window. The guard and the delete are one mechanism.
    """
    writes = _Writes()
    client = _Client()
    monkeypatch.setattr(module, "load_json_to_bq", writes)
    patch(monkeypatch, lambda: _errored())

    ctx = _ctx(client)
    invoke(ctx)

    assert writes.calls == [], f"{name}: wrote a partial snapshot (#896)."
    assert client.deletes() == [], (
        f"{name}: issued a DELETE on the incomplete-fetch path. The stored snapshot is the "
        "good one and this would destroy it."
    )
    assert any("INCOMPLETE" in e for e in ctx.errors), (
        f"{name}: discarded silently. ctx.errors={ctx.errors}"
    )


@pytest.mark.parametrize("name, module, patch, invoke, table", CONVERTED, ids=IDS)
def test_a_failed_delete_is_reported_and_does_not_raise(
    name, module, patch, invoke, table, monkeypatch
):
    """Fails safe. The append already succeeded, so both rows survive and staging still
    selects the newer one — a failed delete costs the space saving, never the data. It must
    not take the run down, and it must not pass silently."""
    writes = _Writes()
    client = _Client(fail=True)
    monkeypatch.setattr(module, "load_json_to_bq", writes)
    patch(monkeypatch, lambda: _ok())

    ctx = _ctx(client)
    invoke(ctx)  # must not raise

    assert ctx.errors, f"{name}: a failed DELETE was swallowed with no error recorded."


def test_a_failed_delete_still_extends_team_ids(monkeypatch):
    """`teams` catches the delete itself instead of letting the outer handler take it.

    That handler has side effects this failure must not trigger: it skips the id extension —
    which `teams.py` states runs EITHER WAY, deliberately — and then spends an extra /teams
    call on the `team_ids_for_league` fallback. Downstream, `coaches`, `transfers` and
    `squads` all fetch by team id, so losing the ids turns a failed space reclaim into a
    run-wide outage for that competition.
    """
    writes = _Writes()
    client = _Client(fail=True)
    monkeypatch.setattr(teams, "load_json_to_bq", writes)
    _patch_teams(monkeypatch, lambda: _ok())
    team_ids: set[int] = set()

    teams.load_teams_merge_and_extend_ids(_ctx(client), "BL1", 78, [2025], 2025, team_ids)

    assert team_ids == {1}, (
        "a failed merge-delete cost the run its team ids "
        f"(got {team_ids}); the id extension must be independent of it."
    )


def test_only_the_three_whole_league_loaders_merge(monkeypatch):
    """COACHES looks identical to the three converted loaders and must NOT merge.

    Behavioural, not a source grep: `coaches` is run exactly as the converted loaders are,
    and asserted to issue no DELETE. `stg_apif__coaches.sql` reads ALL snapshots by CPO
    ruling (escalations.log, 2026-06-23) — a league-keyed delete there destroys ~120 coaches
    whose teams later left our pull.
    """
    writes = _Writes()
    client = _Client()
    monkeypatch.setattr(coaches, "load_json_to_bq", writes)
    monkeypatch.setattr(coaches, "fetch_merged_paged", lambda *a, **k: _ok())

    coaches.load_coaches(_ctx(client), "BL1", {1})

    assert [t for t, _ in writes.calls] == ["RAW_APIF_COACHES"], (
        "coaches did not write its snapshot; the test is not exercising the loader."
    )
    assert client.deletes() == [], (
        "COACHES issued a league-keyed DELETE. `stg_apif__coaches` reads ALL snapshots by "
        "CPO ruling 2026-06-23 to preserve every coach ever seen — this destroys them."
    )


def test_the_merge_helper_is_imported_by_exactly_the_converted_loaders():
    """Pins the converted set against a loader being added quietly.

    Checks the imported NAME in each module's namespace, which is a runtime fact rather than
    a text match — a comment mentioning the helper cannot satisfy it. Honest limit: a module
    reaching it as `bigquery.delete_superseded_league_rows` through a module alias would
    evade this, which is why the behavioural COACHES case above exists alongside it.
    """
    import importlib
    import pkgutil

    from ingestion.api_football import loads

    merging = set()
    for mod in pkgutil.iter_modules(loads.__path__):
        module = importlib.import_module(f"{loads.__name__}.{mod.name}")
        if hasattr(module, "delete_superseded_league_rows"):
            merging.add(mod.name)

    assert merging == {"transfers", "standings", "teams"}, (
        f"the merge-on-write set changed to {sorted(merging)}. Only whole-league snapshot "
        "tables may merge. SQUADS writes a team subset (#37), COACHES is read across ALL "
        "snapshots (CPO 2026-06-23), and PLAYER_PROFILES / PLAYER_TEAMS accumulate per "
        "player — a league-keyed delete erases every player from earlier runs."
    )
