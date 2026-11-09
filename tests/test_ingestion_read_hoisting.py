"""Pins the per-run read hoists by counting the BigQuery queries issued, not by asserting outcomes.

A run-wide coverage cache would be wrong: the completeness check must see Phase 2's writes.
"""

from __future__ import annotations

import types

import pytest

from ingestion.api_football import completeness, ingest_plan
from ingestion.api_football.loads import player_universe, squads


class _CountingClient:
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
        # Schema-less so these tests count queries rather than exercise the two-step pruned read.
        return types.SimpleNamespace(schema=[])

    def count_matching(self, *needles: str) -> int:
        return sum(1 for q in self.queries if all(n in q for n in needles))


def _ctx(client):
    return types.SimpleNamespace(client=client, headers={}, errors=[], tables_loaded=0)


# --- Phase 1: fanout coverage is read once for the run, not once per competition ---


def test_resolve_ingest_mode_issues_no_coverage_query():
    """`resolve_ingest_mode` runs per competition, so a FIXTURE_DETAILS scan in it is quadratic."""
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
    """A default would let the scan creep back with every test still green."""
    client = _CountingClient()
    comp = types.SimpleNamespace(
        league_code="BL1", provider_league_id=78, current_season=2025, status="active"
    )
    with pytest.raises(TypeError):
        ingest_plan.resolve_ingest_mode(client, comp)


def test_completeness_keeps_its_own_coverage_read(monkeypatch):
    """Phase 2 writes FIXTURE_DETAILS after Phase 1's read, so the check reads coverage itself."""
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
    """The hoist is an optimisation for the orchestrator, not a requirement on callers."""
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
    """`_existing_player_ids` reads each loader's own target table, so it is not shared."""
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
    """An explicit None payload means "no prior record" and must not trigger a re-fetch."""
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
    """An injectable-coverage parameter would pass a behavioural test, so the signature is pinned."""
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
    """With a default, dropping the orchestrator's one keyword argument would silently restore the scan."""
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
    """Matches calls by name, so an aliased reader called inside the loop evades it."""
    from ingestion.api_football import orchestrator

    inside = _calls_inside_any_loop(orchestrator._load_api_football)

    assert reader not in inside, (
        f"`{reader}` is called from inside a loop in _load_api_football. It must be computed "
        "ONCE above the loop and passed in — calling it per iteration restores the "
        "O(competitions^2) full-table scan #33 item 1 removed, and no callee-level test can "
        "detect that, because the callee still receives a value every time."
    )


def test_prior_snapshot_readers_still_read_when_not_given_a_payload(monkeypatch):
    """Called in isolation, each reader must still fetch for itself."""
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
