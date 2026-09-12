"""Pin the per-run read hoists (#33 item 1) by COUNTING the BigQuery queries issued.

WHY THIS EXISTS
---------------
Ingestion reads were O(competitions^2): two full-table scans sat inside the per-competition
loop, so every league added made every other league more expensive. `coverage.read_coverage()`
scans all of RAW_APIF_FIXTURE_DETAILS with no league or time filter; `captured_player_team_
seasons()` UNNESTs all of RAW_APIF_PLAYERS. At 45 active competitions that is ~45 scans of each
per run.

Nothing about that is visible from a passing test suite, a green pipeline, or the data. It shows
up only on the bill, and the regression is a one-line change — restore a default argument, or
call the reader "just here", and the loop is quadratic again with every test still green. So
these tests count queries rather than assert outcomes.

THE HAZARD THESE TESTS ALSO GUARD, which is NOT about cost
-----------------------------------------------------------
A run-wide cache would be WRONG. `orchestrator` interleaves these reads with writes to the very
tables being read: Phase 1 reads fanout coverage, Phase 2 WRITES FIXTURE_DETAILS, and the
completeness check then reads coverage again — and it must see Phase 2's writes, because
detecting missing fanout data is its entire job. Cache across that boundary and every run
reports gaps it had just filled.

So `test_completeness_keeps_its_own_coverage_read` is the important one here. The others pin a
cost property; that one pins a correctness property, and it is what should fail if someone
"finishes the job" by hoisting coverage to run scope.
"""

from __future__ import annotations

import types

import pytest

from ingestion.api_football import completeness, ingest_plan
from ingestion.api_football.loads import player_universe, squads


class _CountingClient:
    """Records every query issued so a test can count them by shape."""

    def __init__(self, rows_by_marker=None):
        self.queries: list[str] = []
        self._rows_by_marker = rows_by_marker or {}

    def query(self, sql, job_config=None):
        self.queries.append(sql)
        rows = []
        for marker, marker_rows in self._rows_by_marker.items():
            if marker in sql:
                rows = marker_rows
                break
        return types.SimpleNamespace(result=lambda: iter(rows))

    def get_table(self, table_id):
        # Schema-less on purpose: `read_latest_payload_json` branches on whether an
        # ingest-time column exists, and these tests count queries rather than exercise
        # the two-step pruned read, which `tests/test_latest_payload_read.py` owns.
        return types.SimpleNamespace(schema=[])

    def count_matching(self, *needles: str) -> int:
        return sum(1 for q in self.queries if all(n in q for n in needles))


def _ctx(client):
    return types.SimpleNamespace(client=client, headers={}, errors=[], tables_loaded=0)


# --- Phase 1: fanout coverage is read once for the run, not once per competition ---


def test_resolve_ingest_mode_issues_no_coverage_query():
    """The scan must happen in the caller, above the loop — never in here.

    `resolve_ingest_mode` runs once per competition. Any RAW_APIF_FIXTURE_DETAILS scan
    reachable from it is the quadratic defect, whatever it is called.
    """
    client = _CountingClient()
    comp = types.SimpleNamespace(
        league_code="BL1", provider_league_id=78, current_season=2025, status="active"
    )

    ingest_plan.resolve_ingest_mode(client, comp, {})

    coverage_queries = client.count_matching("FIXTURE_DETAILS", "JSON_QUERY_ARRAY")
    assert coverage_queries == 0, (
        "resolve_ingest_mode issued a RAW_APIF_FIXTURE_DETAILS scan. It is called once per "
        "competition, so that read is O(competitions^2) — the exact defect #33 item 1 removed. "
        f"Queries issued: {client.queries}"
    )


def test_resolve_ingest_mode_requires_coverage_to_be_passed_in():
    """No default. A default would let the scan creep back with every test still green."""
    client = _CountingClient()
    comp = types.SimpleNamespace(
        league_code="BL1", provider_league_id=78, current_season=2025, status="active"
    )
    with pytest.raises(TypeError):
        ingest_plan.resolve_ingest_mode(client, comp)


def test_completeness_keeps_its_own_coverage_read(monkeypatch):
    """THE CORRECTNESS PIN, not a cost one.

    Phase 2 writes RAW_APIF_FIXTURE_DETAILS between Phase 1's coverage read and this one.
    The completeness check exists to notice fanout gaps, so it must observe those writes.
    If someone "finishes the job" by hoisting coverage to run scope to get the count from
    2 to 1, this fails.

    Asserts the CALL, not the source text. The first version of this test grepped
    `inspect.getsource` for "read_coverage(" and passed while the call was removed —
    because that string also appears in a COMMENT inside the same function. A guard that
    matches prose is defeated by a reword, and this one was defeated by a reword that had
    already happened.
    """
    calls: list[str] = []
    monkeypatch.setattr(
        completeness, "read_coverage", lambda client: calls.append("read") or {}
    )
    monkeypatch.setattr(completeness, "skip_completeness_check", lambda: False)
    monkeypatch.setattr(completeness, "selected_competitions", lambda: ([], []))
    monkeypatch.setattr(
        completeness, "read_latest_payload_json", lambda *a, **k: None
    )

    completeness.run_ingest_completeness_checks(_CountingClient())

    assert calls == ["read"], (
        "run_ingest_completeness_checks did not read fanout coverage itself. Phase 2 WRITES "
        "FIXTURE_DETAILS after Phase 1's read, so reusing Phase 1's result here would make "
        "the completeness gate report gaps the same run had already filled."
    )


# --- Phase 3: the captured (team, season) set is read once and kept exact ---


def test_load_squad_players_batch_does_not_reread_when_given_the_set():
    client = _CountingClient()
    ctx = _ctx(client)

    squads.load_squad_players_batch(
        ctx, "BL1", [2025], set(), reference_season=2025, already_captured={(1, 2025)}
    )

    assert client.count_matching("RAW_APIF_PLAYERS", "UNNEST") == 0, (
        "load_squad_players_batch re-read the captured (team, season) set even though the "
        "caller supplied it. That read UNNESTs all of RAW_APIF_PLAYERS and the function runs "
        f"once per competition. Queries issued: {client.queries}"
    )


def test_load_squad_players_batch_still_reads_when_not_given_the_set():
    """The hoist is an optimisation for the orchestrator, not a new requirement on callers."""
    client = _CountingClient()
    ctx = _ctx(client)

    squads.load_squad_players_batch(ctx, "BL1", [2025], set(), reference_season=2025)

    assert client.count_matching("RAW_APIF_PLAYERS", "UNNEST") == 1


# --- Phase 5: one player-universe query for both per-player loaders ---


def test_players_needing_does_not_requery_the_universe_when_given_one():
    client = _CountingClient()

    player_universe.players_needing(
        client, "PLAYER_PROFILES", universe=[(10, "BL1"), (11, "PL")]
    )

    assert client.count_matching("players_payload") == 0, (
        "players_needing recomputed the player universe despite being handed one. That query "
        "UNNESTs all of RAW_APIF_PLAYERS and both per-player loaders need the identical "
        f"answer. Queries issued: {client.queries}"
    )


def test_players_needing_still_reads_the_target_table_per_call():
    """`_existing_player_ids` must NOT be shared — it reads the target, which differs."""
    client = _CountingClient()

    player_universe.players_needing(client, "PLAYER_PROFILES", universe=[(10, "BL1")])

    assert client.count_matching("PLAYER_PROFILES") == 1, (
        "the per-target 'already ingested' read was skipped. It reads the TARGET table, which "
        "differs between PLAYER_PROFILES and PLAYER_TEAMS and is written between them, so it "
        "is not shareable."
    )


# --- Completeness snapshot: one read, three keys ---


def test_prior_snapshot_readers_do_not_requery_when_given_the_payload():
    client = _CountingClient()
    payload = {
        "fixture_statistics_missing": {"BL1": 1},
        "dropped_calls_by_endpoint": {"/players": 2},
        "per_team_missing": {"BL1/players": 3},
    }

    assert completeness.load_prior_fixture_statistics_missing(client, payload) == {"BL1": 1}
    assert completeness.load_prior_dropped_calls(client, payload) == {"/players": 2}
    assert completeness.load_prior_per_team_missing(client, payload) == {"BL1/players": 3}

    assert client.queries == [], (
        "a prior-snapshot reader issued its own query despite being handed the payload. All "
        f"three read different keys out of the SAME row. Queries issued: {client.queries}"
    )


def test_a_first_run_still_costs_one_snapshot_read_not_four(monkeypatch):
    """The regression the first version of the hoist introduced.

    `read_prior_snapshot()` returns None on a FIRST run — no snapshot table yet, or the
    previous run skipped the completeness check. While None doubled as the "caller supplied
    nothing" sentinel, passing that None through made all three readers fetch for
    themselves: 1 hoisted read + 3 re-reads = 4, one MORE than the 3 this change removes,
    in precisely the case every one of those readers documents itself as existing for.

    Counts calls to `read_latest_payload_json`, NOT `client.query`. The first version of
    this test counted queries on the fake client and passed while the defect was
    reintroduced, because that reader reaches BigQuery through the Storage Read API and
    never touches `client.query`. Counting the wrong thing is how a guard reads green
    against the very bug it names.
    """
    fetches: list[str] = []
    monkeypatch.setattr(
        completeness,
        "read_latest_payload_json",
        lambda client, table, *a, **k: fetches.append(table) or None,
    )
    client = _CountingClient()

    assert completeness.load_prior_fixture_statistics_missing(client, None) is None
    assert completeness.load_prior_dropped_calls(client, None) is None
    assert completeness.load_prior_per_team_missing(client, None) is None

    assert fetches == [], (
        "a prior-snapshot reader re-fetched after being handed an explicit None. None is a "
        "legitimate ANSWER ('no prior record'), not the absence of one; only the private "
        f"_UNREAD sentinel means 'unsupplied'. Fetches: {fetches}"
    )


def test_completeness_check_cannot_be_handed_injected_coverage():
    """Structural companion to the correctness pin above.

    The realistic way to break the completeness gate is not to delete its read — it is to
    add `all_covered=None` to this signature and wire the orchestrator to pass Phase 1's
    result, which is the exact optional-parameter shape this branch uses four times
    elsewhere. A behavioural test cannot see that: called with one argument it still takes
    the None branch and still passes. So the SIGNATURE is pinned instead.
    """
    import inspect

    params = list(inspect.signature(completeness.run_ingest_completeness_checks).parameters)
    assert params == ["client"], (
        "run_ingest_completeness_checks accepts something besides `client`: "
        f"{params}. If that is a way to inject already-read coverage, the completeness gate "
        "can be fed Phase 1's PRE-fanout snapshot and will report gaps the same run filled. "
        "This read must stay the function's own."
    )


@pytest.mark.parametrize(
    "func_path, argname",
    [
        ("ingestion.api_football.loads.competition_runner.run_squads_for_competition",
         "already_captured"),
        ("ingestion.api_football.loads.player_profiles.load_player_profiles_global",
         "universe"),
        ("ingestion.api_football.loads.player_teams.load_player_teams_global", "universe"),
    ],
)
def test_hoisted_values_are_required_arguments(func_path, argname):
    """No defaults on the orchestrator-facing hoists.

    Each of these has exactly ONE caller: the orchestrator. With a default, deleting the
    keyword argument at that single call site restores a per-competition or duplicated
    full-table scan and every test in this file still passes, because they all exercise the
    functions in isolation. Without a default it is a TypeError. `resolve_ingest_mode` was
    already protected this way; these three were not.
    """
    import importlib
    import inspect

    module_path, _, name = func_path.rpartition(".")
    func = getattr(importlib.import_module(module_path), name)
    param = inspect.signature(func).parameters[argname]

    assert param.default is inspect.Parameter.empty, (
        f"{name}'s `{argname}` has a default ({param.default!r}). The orchestrator is its "
        "only caller, so a default means the hoist can be silently reverted by deleting one "
        "keyword argument, with the whole suite still green."
    )


def _calls_inside_any_loop(func) -> set[str]:
    """Names of functions called from inside a `for`/`while` body in `func`'s source."""
    import ast
    import inspect
    import textwrap

    tree = ast.parse(textwrap.dedent(inspect.getsource(func)))
    inside: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, (ast.For, ast.While)):
            continue
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                fn = child.func
                if isinstance(fn, ast.Name):
                    inside.add(fn.id)
                elif isinstance(fn, ast.Attribute):
                    inside.add(fn.attr)
    return inside


@pytest.mark.parametrize(
    "reader",
    ["read_coverage", "captured_player_team_seasons", "query_player_universe"],
)
def test_the_hoisted_reads_are_not_issued_inside_a_loop(reader):
    """The property this whole change is about, pinned where the defect actually lives.

    Requiring the argument closes only the narrowest revert path — deleting the
    keyword. Move the computation back INSIDE the
    per-competition loop and keep passing it, and every other test in this file stays green
    while the O(competitions^2) scan is fully restored: the callee still receives a value on
    every call, so no callee-level assertion can see it. The defect is in the CALLER's call
    placement, so that is what this checks.

    Structural rather than behavioural, deliberately. "Computed once, above the loop" is a
    statement about code shape; the behavioural equivalent means mocking ~20 collaborators
    to drive `_load_api_football` end to end, which would be a fragile test of the wrong
    thing.

    KNOWN LIMIT, stated rather than left implicit: this matches calls by NAME, so aliasing
    the reader (`_rc = read_coverage`) and calling the alias inside the loop evades it. That
    is a deliberate act, not the accidental revert this guards against.
    """
    from ingestion.api_football import orchestrator

    inside = _calls_inside_any_loop(orchestrator._load_api_football)

    assert reader not in inside, (
        f"`{reader}` is called from inside a loop in _load_api_football. It must be computed "
        "ONCE above the loop and passed in — calling it per iteration restores the "
        "O(competitions^2) full-table scan #33 item 1 removed, and no callee-level test can "
        "detect that, because the callee still receives a value every time."
    )


def test_prior_snapshot_readers_still_read_when_not_given_a_payload(monkeypatch):
    """Called in isolation — a test, a script — each must still fetch for itself.

    Counts calls to `read_latest_payload_json`, not raw queries: that reader reaches
    BigQuery through the Storage Read API rather than `client.query`, and how it gets
    there is `tests/test_latest_payload_read.py`'s business, not this file's.
    """
    calls: list[str] = []
    monkeypatch.setattr(
        completeness,
        "read_latest_payload_json",
        lambda client, table, *a, **k: calls.append(table) or {"dropped_calls_by_endpoint": {}},
    )

    completeness.load_prior_dropped_calls(_CountingClient())

    assert calls == [completeness.COMPLETENESS_SNAPSHOT_TABLE], (
        "load_prior_dropped_calls no longer fetches for itself when given no payload. The "
        "shared-payload argument is an optimisation for the orchestrator, not a new "
        f"requirement on every caller. Fetches: {calls}"
    )
