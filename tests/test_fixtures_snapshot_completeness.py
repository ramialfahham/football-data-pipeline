"""Tests for the completeness carry-forward in loads/fixtures.py: each snapshot written is complete."""

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
    """Returns (merged, team_ids, fixture_ids, mock_fetch, mock_bq) from a run with mocked I/O."""
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
        assert mock_fetch.call_count == 1
        assert mock_fetch.call_args_list[0][0][2]["season"] == _CURRENT_SEASON
        assert mock_bq.call_count == 1
        assert _written_seasons(mock_bq) == {2022, 2023, 2024}

    def test_team_ids_scoped_to_fetched_season(self):
        # Carried-forward teams must not widen the squad-catch-up team set.
        ctx = _make_ctx()
        cached = _sample_response()
        fresh_2024 = _fixtures_for_season(cached, _CURRENT_SEASON)
        _, team_ids, fixture_ids, _, mock_bq = _run(
            ctx, cached, api_side_effect=[_envelope(fresh_2024)], seasons=[_CURRENT_SEASON]
        )
        assert _written_seasons(mock_bq) == {2022, 2023, 2024}
        assert team_ids == _CURRENT_TEAMS
        assert fixture_ids == {_CURRENT_FIXTURE_ID}
        assert team_ids.isdisjoint(_HISTORICAL_TEAMS)

    def test_full_mode_carry_forward_is_noop(self):
        # Full mode reuses every complete historical season from cache and fetches the current one.
        ctx = _make_ctx()
        cached = _sample_response()
        fresh_2024 = _fixtures_for_season(cached, _CURRENT_SEASON)
        _, team_ids, _, mock_fetch, mock_bq = _run(
            ctx, cached, api_side_effect=[_envelope(fresh_2024)], seasons=[2022, 2023, 2024]
        )
        assert mock_fetch.call_count == 1
        assert _written_seasons(mock_bq) == {2022, 2023, 2024}
        assert team_ids == _CURRENT_TEAMS | _HISTORICAL_TEAMS

    def test_thin_cache_carries_nothing(self):
        # A thin latest snapshot cannot conjure history; only a full-mode run re-establishes it.
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
    """A failed or empty fresh fetch must not overwrite the last good snapshot."""

    def test_empty_fresh_fetch_does_not_write(self):
        # The current season comes back empty while a complete prior snapshot exists.
        ctx = _make_ctx()
        cached = _sample_response()
        _, team_ids, fixture_ids, _, mock_bq = _run(
            ctx, cached, api_side_effect=[_envelope([])], seasons=[_CURRENT_SEASON]
        )
        mock_bq.assert_not_called()
        assert team_ids == set() and fixture_ids == set()
        assert any("empty response" in e for e in ctx.errors)

    def test_quota_exhausted_before_fetch_does_not_write(self):
        # With nothing fetched, carry-forward must not re-stamp the prior snapshot as today's.
        ctx = _make_ctx()
        cached = _sample_response()
        with patch("ingestion.api_football.quota._http_quota_exhausted", True):
            _, team_ids, _, mock_fetch, mock_bq = _run(
                ctx, cached, api_side_effect=[], seasons=[_CURRENT_SEASON]
            )
        mock_fetch.assert_not_called()
        mock_bq.assert_not_called()
        assert team_ids == set()
