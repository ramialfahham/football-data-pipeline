"""Tests for player_squads.select_squad_catchup_team_ids (finished-comp squad catch-up policy).

Pure policy, no I/O: given finished (poll-mode) competitions and what we already hold, decide
which teams still need a /players/squads snapshot. A squad is a team property, so the policy
dedupes across competitions and skips teams that are active elsewhere or already captured for
that season. Club and national comps are treated identically — only team_ids matter here.
"""

from __future__ import annotations

import types

from ingestion.api_football.loads.player_squads import (
    captured_team_seasons,
    select_squad_catchup_team_ids,
)
from ingestion.api_football.settings import DATASET_ID, GCP_PROJECT_ID


def test_empty_finished_comps_returns_empty():
    assert select_squad_catchup_team_ids([], set(), set()) == []


def test_captures_finished_comp_teams_when_none_held():
    plan = select_squad_catchup_team_ids(
        finished_comps=[("PL", 2025, {10, 11, 12})],
        active_team_ids=set(),
        already_captured=set(),
    )
    assert plan == [("PL", 2025, {10, 11, 12})]


def test_skips_teams_active_in_a_full_mode_comp():
    # team 11 still plays a full-mode comp this run (e.g. its continental cup) -> captured in-season.
    plan = select_squad_catchup_team_ids(
        finished_comps=[("PL", 2025, {10, 11, 12})],
        active_team_ids={11},
        already_captured=set(),
    )
    assert plan == [("PL", 2025, {10, 12})]


def test_skips_teams_already_held_for_that_season():
    plan = select_squad_catchup_team_ids(
        finished_comps=[("PL", 2025, {10, 11, 12})],
        active_team_ids=set(),
        already_captured={(10, 2025), (12, 2025)},
    )
    assert plan == [("PL", 2025, {11})]


def test_held_for_other_season_is_still_fetched():
    # We hold team 10's 2024 squad, but its 2025 season just finished and is not held -> fetch.
    plan = select_squad_catchup_team_ids(
        finished_comps=[("PL", 2025, {10})],
        active_team_ids=set(),
        already_captured={(10, 2024)},
    )
    assert plan == [("PL", 2025, {10})]


def test_dedupes_team_across_finished_comps():
    # Club 10 is in both PL and the domestic cup FAC, both finished -> fetched once, owned by the
    # first comp in order; FAC keeps only its remaining team.
    plan = select_squad_catchup_team_ids(
        finished_comps=[("PL", 2025, {10, 11}), ("FAC", 2025, {10, 20})],
        active_team_ids=set(),
        already_captured=set(),
    )
    assert plan == [("PL", 2025, {10, 11}), ("FAC", 2025, {20})]


def test_drops_comp_that_needs_nothing():
    plan = select_squad_catchup_team_ids(
        finished_comps=[("PL", 2025, {10}), ("BL1", 2025, {10})],
        active_team_ids=set(),
        already_captured={(10, 2025)},
    )
    assert plan == []


def test_national_comp_teams_are_treated_like_any_other():
    # WC is a national-team comp; its national sides catch up the same way clubs do.
    plan = select_squad_catchup_team_ids(
        finished_comps=[("WC", 2022, {1, 2, 3})],
        active_team_ids=set(),
        already_captured={(2, 2022)},
    )
    assert plan == [("WC", 2022, {1, 3})]


# --- captured_team_seasons: BigQuery read of already-stored (team, season) pairs ---
# Fake client/ctx so the Python row-handling is exercised with NO network. The SQL's JSON-path
# extraction itself cannot run offline; it is validated against real RAW_APIF_SQUADS separately.


class _FakeResult:
    def __init__(self, rows):
        self._rows = rows

    def result(self):
        return self._rows


class _FakeClient:
    def __init__(self, rows=None, raise_exc=None):
        self._rows = rows or []
        self._raise = raise_exc
        self.last_sql = None

    def query(self, sql):
        self.last_sql = sql
        if self._raise is not None:
            raise self._raise
        return _FakeResult(self._rows)


def _fake_ctx(rows=None, raise_exc=None):
    return types.SimpleNamespace(client=_FakeClient(rows=rows, raise_exc=raise_exc), errors=[])


def _row(team_id, season):
    return types.SimpleNamespace(team_id=team_id, season=season)


def test_captured_team_seasons_returns_pairs():
    ctx = _fake_ctx(rows=[_row(10, 2025), _row(11, 2025), _row(10, 2024)])
    assert captured_team_seasons(ctx) == {(10, 2025), (11, 2025), (10, 2024)}
    assert ctx.errors == []


def test_captured_team_seasons_skips_null_rows():
    ctx = _fake_ctx(rows=[_row(10, 2025), _row(None, 2025), _row(11, None)])
    assert captured_team_seasons(ctx) == {(10, 2025)}


def test_captured_team_seasons_failopen_on_query_error():
    # A read failure must not abort the run; return empty (re-capture is the safe direction).
    ctx = _fake_ctx(raise_exc=RuntimeError("boom"))
    assert captured_team_seasons(ctx) == set()
    assert any("captured-seasons read failed" in e for e in ctx.errors)


def test_captured_team_seasons_query_is_fully_qualified():
    # Regression guard: a bare table name (RAW_APIF_SQUADS) fails at runtime; the read must
    # reference project.dataset (matches _fq in loads/player_universe.py).
    ctx = _fake_ctx(rows=[])
    captured_team_seasons(ctx)
    assert f"{GCP_PROJECT_ID}.{DATASET_ID}." in ctx.client.last_sql
    assert "RAW_APIF_SQUADS" in ctx.client.last_sql


# --- load_player_squads_batch: catch-up writes must be COMPLETE per competition ---
# A quota cut mid-comp under require_complete must discard the partial (stg_apif__squads keeps
# only the latest snapshot per league_code; a finished comp is never re-fetched whole, so a
# partial would be silently dropped). In-season (require_complete=False) keeps writing partials —
# the next complete snapshot heals them.


def _squad_ctx():
    return types.SimpleNamespace(
        headers={}, errors=[], client=None, add_loaded=lambda n: None
    )


def _patch_quota_cut_after_first(monkeypatch):
    from ingestion.api_football import quota as q
    from ingestion.api_football.loads import player_squads as ps

    monkeypatch.setattr(q, "_http_quota_exhausted", False)

    def fake_squad(headers, team_id, errors, error_context=""):
        monkeypatch.setattr(q, "_http_quota_exhausted", True)  # exhaust after the first fetch
        # The helper returns (rows, complete). COMPLETE deliberately: this test is about the QUOTA
        # cut mid-competition, not about a failed fetch, and the two paths must stay separable.
        return [{"players": []}], True

    monkeypatch.setattr(ps, "squads_response_for_team", fake_squad)
    written = []
    monkeypatch.setattr(ps, "load_json_to_bq", lambda *a, **k: written.append(k))
    return ps, written


def test_catchup_discards_partial_when_require_complete(monkeypatch):
    ps, written = _patch_quota_cut_after_first(monkeypatch)
    ctx = _squad_ctx()
    ps.load_player_squads_batch(ctx, "PL", {10, 11, 12}, season=2025, require_complete=True)
    assert written == []  # partial discarded, not persisted
    assert any("partial discarded" in e for e in ctx.errors)


def test_inseason_writes_partial_when_not_require_complete(monkeypatch):
    ps, written = _patch_quota_cut_after_first(monkeypatch)
    ctx = _squad_ctx()
    ps.load_player_squads_batch(ctx, "PL", {10, 11, 12}, season=2025, require_complete=False)
    assert len(written) == 1  # partial persisted (in-season behaviour, healed next run)
