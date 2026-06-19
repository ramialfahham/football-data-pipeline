"""Tests for the completeness carry-forward in loads/fixtures.py.

The append-only fixtures table's contract is that every written snapshot is COMPLETE — the latest
row alone carries full history, which the full-refresh fct_fixture depends on. A poll/idle run only
fetches the current season (catalog collapses seasons_list to keep squad-catch-up team_ids scoped to
the latest season), so without carry-forward it would write a current-season-only snapshot and silently
drop history (the idle-mode regression these tests guard against).

These tests pin:
- a poll-style single-season fetch carries forward the prior snapshot's other seasons -> COMPLETE write,
- team_ids / fixture_ids stay scoped to the freshly fetched season (carried-forward teams excluded),
- full mode is a no-op (its season list already covers every prior season),
- an empty / thin cache carries nothing (recovery is what re-establishes a complete latest snapshot),
- an empty / quota-exhausted FRESH fetch writes NOTHING — the prior good snapshot stays "latest"
  (data-engineer review Finding 2).

Per the CPO sample-payload rule (2026-06-12), the parsing/merge behaviour is exercised against a REAL
committed `/fixtures` payload (tests/fixtures/apif/bl1_fixtures_next_merged.json — a slice captured from
RAW), sliced by season to simulate the cached snapshot vs a single-season fetch. All BigQuery and HTTP
interactions are mocked — no live GCP connection required.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from ingestion.api_football.loads.fixtures import fetch_merge_and_persist_fixtures

_SAMPLE_PATH = Path(__file__).parent / "fixtures" / "apif" / "bl1_fixtures_next_merged.json"

# Real team ids in the committed sample (one fixture per season):
#   2022 -> Eintracht Frankfurt (169) vs Bayern (157)
#   2023 -> Werder Bremen (162)     vs Bayern (157)
#   2024 -> Borussia M'gladbach (163) vs Bayer Leverkusen (168)  <- the "current" season
_CURRENT_SEASON = 2024
_CURRENT_TEAMS = {163, 168}
_CURRENT_FIXTURE_ID = 1223975
_HISTORICAL_TEAMS = {157, 162, 169}


def _sample_response() -> list:
    return json.loads(_SAMPLE_PATH.read_text(encoding="utf-8"))["response"]


def _fixtures_for_season(response: list, season: int) -> list:
    return [f for f in response if f.get("league", {}).get("season") == season]


def _make_ctx():
    ctx = MagicMock()
    ctx.errors = []
    ctx.headers = {"x-apisports-key": "test"}
    return ctx


def _envelope(items: list) -> dict:
    return {
        "response": items,
        "errors": [],
        "results": len(items),
        "paging": {"current": 1, "total": 1},
    }


def _run(ctx, cached_items, api_side_effect, seasons, env_extra=None):
    """Drive the loader with a mocked cache read + mocked API; return (merged, team_ids,
    fixture_ids, mock_fetch, mock_bq)."""
    env = {"API_FOOTBALL_FIXTURES_MODE": "season"}
    if env_extra:
        env.update(env_extra)
    with patch.dict("os.environ", env, clear=False):
        with patch(
            "ingestion.api_football.loads.fixtures.read_latest_payload_json",
            return_value=_envelope(cached_items),
        ):
            with patch(
                "ingestion.api_football.loads.fixtures.fetch_merged_paged",
                side_effect=api_side_effect,
            ) as mock_fetch:
                with patch(
                    "ingestion.api_football.loads.fixtures.load_json_to_bq"
                ) as mock_bq:
                    merged, team_ids, fixture_ids = fetch_merge_and_persist_fixtures(
                        ctx, "BL1", 78, seasons
                    )
    return merged, team_ids, fixture_ids, mock_fetch, mock_bq


def _written_seasons(mock_bq) -> set:
    payload = mock_bq.call_args[0][2]
    return {f["league"]["season"] for f in payload["response"]}


class TestCarryForwardCompleteness:
    def test_poll_single_season_carries_forward_history(self):
        # Poll/idle: fetch only the current season; the cached snapshot holds all three.
        ctx = _make_ctx()
        cached = _sample_response()
        fresh_2024 = _fixtures_for_season(cached, _CURRENT_SEASON)
        _, _, _, mock_fetch, mock_bq = _run(
            ctx, cached, api_side_effect=[_envelope(fresh_2024)], seasons=[_CURRENT_SEASON]
        )
        # Only the current season is fetched from the API...
        assert mock_fetch.call_count == 1
        assert mock_fetch.call_args_list[0][0][2]["season"] == _CURRENT_SEASON
        # ...but the WRITTEN snapshot is complete: every cached season is preserved.
        assert mock_bq.call_count == 1
        assert _written_seasons(mock_bq) == {2022, 2023, 2024}

    def test_team_ids_scoped_to_fetched_season(self):
        # Carried-forward historical teams must NOT widen the squad-catch-up team set.
        ctx = _make_ctx()
        cached = _sample_response()
        fresh_2024 = _fixtures_for_season(cached, _CURRENT_SEASON)
        _, team_ids, fixture_ids, _, mock_bq = _run(
            ctx, cached, api_side_effect=[_envelope(fresh_2024)], seasons=[_CURRENT_SEASON]
        )
        # The written snapshot still carries the historical seasons (completeness)...
        assert _written_seasons(mock_bq) == {2022, 2023, 2024}
        # ...but team_ids / fixture_ids reflect only the freshly fetched current season.
        assert team_ids == _CURRENT_TEAMS
        assert fixture_ids == {_CURRENT_FIXTURE_ID}
        assert team_ids.isdisjoint(_HISTORICAL_TEAMS)

    def test_full_mode_carry_forward_is_noop(self):
        # Full mode reuses every complete historical season from cache + fetches the current one;
        # nothing is carried forward, and the all-season team_ids are unchanged from prior behaviour.
        ctx = _make_ctx()
        cached = _sample_response()
        fresh_2024 = _fixtures_for_season(cached, _CURRENT_SEASON)
        _, team_ids, _, mock_fetch, mock_bq = _run(
            ctx, cached, api_side_effect=[_envelope(fresh_2024)], seasons=[2022, 2023, 2024]
        )
        # 2022/2023 are complete (FT) in cache -> reused; only 2024 hits the API.
        assert mock_fetch.call_count == 1
        assert _written_seasons(mock_bq) == {2022, 2023, 2024}
        assert team_ids == _CURRENT_TEAMS | _HISTORICAL_TEAMS

    def test_thin_cache_carries_nothing(self):
        # Recovery precondition: a thin latest snapshot (already collapsed to the current season)
        # cannot conjure history; the write stays thin until a full-mode run re-establishes a
        # complete snapshot. The PR2 DQ test then guards against this state shipping.
        ctx = _make_ctx()
        fresh_2024 = _fixtures_for_season(_sample_response(), _CURRENT_SEASON)
        _, _, _, _, mock_bq = _run(
            ctx, fresh_2024, api_side_effect=[_envelope(fresh_2024)], seasons=[_CURRENT_SEASON]
        )
        assert _written_seasons(mock_bq) == {2024}

    def test_empty_cache_carries_nothing(self):
        ctx = _make_ctx()
        fresh_2024 = _fixtures_for_season(_sample_response(), _CURRENT_SEASON)
        _, _, _, _, mock_bq = _run(
            ctx, [], api_side_effect=[_envelope(fresh_2024)], seasons=[_CURRENT_SEASON]
        )
        assert _written_seasons(mock_bq) == {2024}


class TestEmptyFreshFetchWritesNothing:
    """Finding 2: a failed/empty fresh fetch must not overwrite the last good snapshot."""

    def test_empty_fresh_fetch_does_not_write(self):
        # The current season comes back empty (e.g. provider hiccup); a complete prior snapshot exists.
        ctx = _make_ctx()
        cached = _sample_response()
        _, team_ids, fixture_ids, _, mock_bq = _run(
            ctx, cached, api_side_effect=[_envelope([])], seasons=[_CURRENT_SEASON]
        )
        # No snapshot written -> the prior complete latest row is preserved; the run logged an error.
        mock_bq.assert_not_called()
        assert team_ids == set() and fixture_ids == set()
        assert any("empty response" in e for e in ctx.errors)

    def test_quota_exhausted_before_fetch_does_not_write(self):
        # Quota runs out before the poll fetch: the loop breaks, nothing is fetched, and the
        # carry-forward must NOT re-stamp the entire prior snapshot as today's.
        ctx = _make_ctx()
        cached = _sample_response()
        with patch("ingestion.api_football.quota._http_quota_exhausted", True):
            _, team_ids, _, mock_fetch, mock_bq = _run(
                ctx, cached, api_side_effect=[], seasons=[_CURRENT_SEASON]
            )
        mock_fetch.assert_not_called()
        mock_bq.assert_not_called()
        assert team_ids == set()
